import os
import sys
import time
import shutil
import tempfile
import unittest
import unittest.mock
import signal
import sqlite3
import subprocess
import importlib.util
import importlib.machinery
from pathlib import Path
from datetime import datetime, timezone

daemon_path = Path(__file__).resolve().parent.parent / "files" / "system" / "usr" / "bin" / "midikeep-daemon"
loader = importlib.machinery.SourceFileLoader("midikeep_daemon", str(daemon_path))
spec = importlib.util.spec_from_loader("midikeep_daemon", loader)
daemon = importlib.util.module_from_spec(spec)
loader.exec_module(daemon)
cli_path = Path(__file__).resolve().parent.parent / "files" / "system" / "usr" / "bin" / "midikeep"
cli_loader = importlib.machinery.SourceFileLoader("midikeep_cli", str(cli_path))
cli_spec = importlib.util.spec_from_loader("midikeep_cli", cli_loader)
midikeep_cli = importlib.util.module_from_spec(cli_spec)
cli_loader.exec_module(midikeep_cli)



class TestDatabaseIndex(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = Path(self.temp_dir) / "test_index.db"
        self.db = daemon.DatabaseIndex(self.db_path)

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_schema_and_insert(self):
        start_t = datetime.now(timezone.utc).isoformat()
        end_t = datetime.now(timezone.utc).isoformat()
        file_p = "/tmp/test_session.mid"

        row_id = self.db.insert_session(
            start_time=start_t,
            end_time=end_t,
            duration_seconds=125.5,
            active_play_seconds=95.2,
            note_count=42,
            device_name="Test Controller",
            file_path=file_p,
            key_signature="C Major",
            tempo_bpm=120.0,
            starred=True,
            notes="Take 1",
        )
        self.assertGreater(row_id, 0)

        with self.db._get_connection() as conn:
            row = conn.execute("SELECT * FROM sessions WHERE id = ?", (row_id,)).fetchone()
            self.assertIsNotNone(row)
            self.assertEqual(row["device_name"], "Test Controller")
            self.assertEqual(row["note_count"], 42)
            self.assertEqual(row["file_path"], file_p)
            self.assertEqual(row["key_signature"], "C Major")
            self.assertEqual(row["starred"], 1)
            self.assertEqual(row["duration_seconds"], 125.5)
            self.assertEqual(row["active_play_seconds"], 95.2)


class TestMidiFileBuilder(unittest.TestCase):
    def test_vlq_encoding(self):
        cases = [
            (0, b"\x00"),
            (0x40, b"\x40"),
            (0x7F, b"\x7F"),
            (0x80, b"\x81\x00"),
            (0x2000, b"\xC0\x00"),
            (0x3FFF, b"\xFF\x7F"),
            (0x4000, b"\x81\x80\x00"),
        ]
        for val, expected in cases:
            self.assertEqual(daemon.encode_vlq(val), expected, f"Failed for {val}")

    def test_build_midi_file(self):
        # Middle C Note On and Note Off
        events = [
            (0.0, bytes([0x90, 60, 100])),
            (0.5, bytes([0x80, 60, 64])),
        ]
        midi_data = daemon.build_midi_file(events, division=480, tempo_bpm=120.0, track_name="Unit Test")
        self.assertTrue(midi_data.startswith(b"MThd"))
        self.assertIn(b"MTrk", midi_data)
        # Verify End of Track meta event exists
        self.assertTrue(midi_data.endswith(b"\x00\xFF\x2F\x00"))


class TestKeyEstimation(unittest.TestCase):
    def test_c_major(self):
        # C major scale: C(60), D(62), E(64), F(65), G(67), A(69), B(71), C(72)
        notes = [60, 62, 64, 65, 67, 69, 71, 72] * 4
        key = daemon.estimate_key(notes)
        self.assertEqual(key, "C Major")

    def test_a_minor(self):
        # A minor scale: A(69), B(71), C(72), D(74), E(76), F(77), G(79), A(81)
        notes = [69, 71, 72, 74, 76, 77, 79, 81] * 4
        key = daemon.estimate_key(notes)
        self.assertEqual(key, "A Minor")

    def test_insufficient_notes(self):
        self.assertIsNone(daemon.estimate_key([60, 62]))


class TestActiveSessionAndSilence(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.data_dir = Path(self.temp_dir)
        self.sessions_dir = self.data_dir / "sessions"
        self.journal_dir = self.data_dir / "journal"
        self.db = daemon.DatabaseIndex(self.data_dir / "index.db")

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_session_lifecycle_and_unclosed_notes(self):
        start_wall = datetime.now(timezone.utc)
        mono_t = 1000.0

        session = daemon.ActiveSession(
            start_wall_time=start_wall,
            start_mono_time=mono_t,
            device_name="Test Synth",
            sessions_dir=self.sessions_dir,
            journal_dir=self.journal_dir,
        )

        # Send Note-On C4
        mono_t += 0.1
        session.record_event(bytes([0x90, 60, 100]), mono_t, "Test Synth")
        self.assertEqual(session.note_count, 1)
        self.assertIn((0, 60), session.active_notes)

        # Send Note-On E4 (without releasing C4)
        mono_t += 0.5
        session.record_event(bytes([0x90, 64, 100]), mono_t, "Test Synth")
        self.assertEqual(session.note_count, 2)
        self.assertEqual(len(session.active_notes), 2)

        # Release E4
        mono_t += 0.5
        session.record_event(bytes([0x80, 64, 64]), mono_t, "Test Synth")
        self.assertEqual(len(session.active_notes), 1)  # C4 still open!

        # Finalize session (C4 should receive synthesized Note-Off)
        mono_t += 1.0
        final_file = session.finalize(self.db, mono_t)

        self.assertTrue(Path(final_file).exists())
        self.assertGreater(Path(final_file).stat().st_size, 0)

        # Verify DB entry
        with self.db._get_connection() as conn:
            row = conn.execute("SELECT * FROM sessions WHERE file_path = ?", (final_file,)).fetchone()
            self.assertIsNotNone(row)
            self.assertEqual(row["note_count"], 2)
            self.assertEqual(row["device_name"], "Test Synth")
            self.assertAlmostEqual(row["duration_seconds"], 2.1, places=1)


class TestCrashResilience(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.data_dir = Path(self.temp_dir)
        self.sessions_dir = self.data_dir / "sessions"
        self.journal_dir = self.data_dir / "journal"
        self.db = daemon.DatabaseIndex(self.data_dir / "index.db")

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_journal_recovery_on_crash(self):
        start_wall = datetime.now(timezone.utc)
        mono_t = 2000.0

        session = daemon.ActiveSession(
            start_wall_time=start_wall,
            start_mono_time=mono_t,
            device_name="Crash Device",
            sessions_dir=self.sessions_dir,
            journal_dir=self.journal_dir,
        )

        # Send a few notes
        for note in [60, 62, 64, 65, 67, 69, 71, 72]:
            mono_t += 0.1
            session.record_event(bytes([0x90, note, 100]), mono_t)
            mono_t += 0.1
            session.record_event(bytes([0x80, note, 64]), mono_t)

        session.flush_journal()
        journal_file = session.journal_file
        target_file = session.target_file

        self.assertTrue(journal_file.exists())
        # Simulate crash: do NOT call session.finalize! Close the file handle to simulate process death
        if session.journal_handle:
            session.journal_handle.close()

        # Run recovery
        daemon.recover_orphaned_journals(self.journal_dir, self.db)

        # Journal file should be cleaned up
        self.assertFalse(journal_file.exists())

        # Recovered MIDI file should now exist!
        self.assertTrue(target_file.exists())
        self.assertGreater(target_file.stat().st_size, 0)

        # Check DB index
        with self.db._get_connection() as conn:
            row = conn.execute("SELECT * FROM sessions WHERE file_path = ?", (str(target_file),)).fetchone()
            self.assertIsNotNone(row)
            self.assertEqual(row["note_count"], 8)
            self.assertEqual(row["device_name"], "Crash Device")
            self.assertEqual(row["notes"], "Recovered after system restart")


class TestAlsaSequencerIntegration(unittest.TestCase):
    def test_alsa_loopback_and_filtering(self):
        # Test ALSA sequencer manager end-to-end
        try:
            alsa = daemon.AlsaSequencerManager(client_name="midikeep_test")
        except Exception as e:
            self.skipTest(f"ALSA sequencer not accessible in this environment: {e}")

        try:
            # Connect our input port to itself for loopback testing
            res = alsa.asound.snd_seq_connect_from(
                alsa.seq, alsa.my_port_id, alsa.my_client_id, alsa.my_port_id
            )
            self.assertEqual(res, 0)

            # Construct Note-On event: 0x90, 60, 100
            ev_buf = (daemon.ctypes.c_byte * 256)()
            encode_res = alsa.asound.snd_midi_event_encode(
                alsa.parser, bytes([0x90, 60, 100]), 3, ev_buf
            )
            self.assertEqual(encode_res, 3)

            # Route to self: direct queue (253), source and dest set to our client:port
            ev_buf[3] = 253
            ev_buf[12] = alsa.my_client_id
            ev_buf[13] = alsa.my_port_id
            ev_buf[14] = alsa.my_client_id
            ev_buf[15] = alsa.my_port_id

            out_res = alsa.asound.snd_seq_event_output_direct(alsa.seq, ev_buf)
            self.assertGreater(out_res, 0)

            # Read back using read_event (draining any announcements)
            midi_received = None
            for _ in range(10):
                ev = alsa.read_event()
                if not ev:
                    break
                ev_type, src_addr, midi_bytes = ev
                if midi_bytes:
                    midi_received = midi_bytes
                    break
            self.assertEqual(midi_received, bytes([0x90, 60, 100]))

        finally:
            alsa.close()



class TestLiveDaemonE2E(unittest.TestCase):
    def test_live_daemon_recording(self):
        test_dir = Path(tempfile.mkdtemp())
        daemon_bin = daemon_path.resolve()

        proc = subprocess.Popen(
            [str(daemon_bin), "--data-dir", str(test_dir), "--silence-threshold", "1", "-v"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        try:
            time.sleep(0.8)
            pid_file = test_dir / "midikeep.pid"
            test_pid = pid_file.read_text().strip() if pid_file.exists() else str(proc.pid)
            
            # Use aconnect -l to find client matching test_pid
            out = subprocess.check_output(["aconnect", "-l"], text=True)
            midikeep_port = None
            current_client = None
            for line in out.splitlines():
                if line.startswith("client "):
                    cid = line.split()[1].rstrip(":")
                    if f"pid={test_pid}" in line:
                        current_client = cid
                elif current_client and "in" in line:
                    pid = line.split()[0]
                    midikeep_port = f"{current_client}:{pid}"
                    break
            self.assertIsNotNone(midikeep_port, "Could not find midikeep port")

            # Create test midi
            test_midi = test_dir / "input.mid"
            events = [
                (0.0, bytes([0x90, 60, 100])),
                (0.1, bytes([0x80, 60, 64])),
                (0.1, bytes([0x90, 64, 100])),
                (0.1, bytes([0x80, 64, 64])),
                (0.1, bytes([0x90, 67, 100])),
                (0.1, bytes([0x80, 67, 64])),
                (0.1, bytes([0x90, 72, 100])),
                (0.1, bytes([0x80, 72, 64])),
            ]
            with open(test_midi, "wb") as f:
                f.write(daemon.build_midi_file(events))

            subprocess.run(["aplaymidi", "-p", midikeep_port, str(test_midi)], check=True)
            time.sleep(2.0) # Wait for 1s silence threshold

            # Verify files
            sessions = list((test_dir / "sessions").glob("**/*.mid"))
            self.assertEqual(len(sessions), 1)

            # Verify SQLite
            conn = sqlite3.connect(str(test_dir / "index.db"))
            conn.row_factory = sqlite3.Row
            rows = conn.execute("SELECT * FROM sessions").fetchall()
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["note_count"], 4)
            self.assertEqual(rows[0]["key_signature"], "C Major")
            conn.close()

        finally:
            proc.terminate()
            try:
                proc.communicate(timeout=3)
            except Exception:
                proc.kill()
            shutil.rmtree(test_dir)


class TestMarkerAndRestart(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.data_dir = Path(self.temp_dir)
        self.sessions_dir = self.data_dir / "sessions"
        self.journal_dir = self.data_dir / "journal"
        self.db = daemon.DatabaseIndex(self.data_dir / "index.db")

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_marker_meta_event_and_starring(self):
        start_wall = datetime.now(timezone.utc)
        mono_t = 1000.0

        session = daemon.ActiveSession(
            start_wall_time=start_wall,
            start_mono_time=mono_t,
            device_name="Test Controller",
            sessions_dir=self.sessions_dir,
            journal_dir=self.journal_dir,
        )

        mono_t += 0.2
        session.record_event(bytes([0x90, 60, 100]), mono_t)
        mono_t += 0.5
        # Add clapper marker
        session.add_marker("Clapper ★", mono_t)
        self.assertTrue(session.starred)
        self.assertIn("Clapper ★", session.markers)

        mono_t += 0.5
        session.record_event(bytes([0x80, 60, 64]), mono_t)
        final_file = session.finalize(self.db, mono_t)

        # Verify MIDI file contains standard MIDI marker 0xFF 0x06
        data = Path(final_file).read_bytes()
        self.assertIn(b"\xFF\x06", data)
        self.assertIn("Clapper".encode("utf-8"), data)

        # Verify database entry has starred = 1
        with self.db._get_connection() as conn:
            row = conn.execute("SELECT * FROM sessions WHERE file_path = ?", (final_file,)).fetchone()
            self.assertEqual(row["starred"], 1)
            self.assertIn("Clapper", row["notes"])

    def test_comment_marker_in_daemon_and_smf(self):
        d = daemon.MidikeepDaemon(data_dir=self.data_dir)
        d.active_session = daemon.ActiveSession(
            start_wall_time=datetime.now(timezone.utc),
            start_mono_time=1000.0,
            device_name="Test Controller",
            sessions_dir=self.sessions_dir,
            journal_dir=self.journal_dir,
        )
        d.active_session.record_event(bytes([0x90, 60, 100]), 1000.1)

        # Write marker.msg with custom comment
        marker_file = self.data_dir / "marker.msg"
        marker_file.write_text("Verse 2 melody idea", encoding="utf-8")

        # Trigger handle_sigusr1
        d.handle_sigusr1(signal.SIGUSR1, None)

        # marker.msg should be consumed and deleted
        self.assertFalse(marker_file.exists())

        # Session should have the marker
        self.assertTrue(d.active_session.starred)
        self.assertIn("Clapper: Verse 2 melody idea", d.active_session.markers)

        # Finalize and verify SMF and DB
        final_file = d.active_session.finalize(self.db, 1001.0)
        data = Path(final_file).read_bytes()
        self.assertIn(bytes([0xFF, 0x06]), data)
        self.assertIn("Verse 2 melody idea".encode("utf-8"), data)

        with self.db._get_connection() as conn:
            row = conn.execute("SELECT * FROM sessions WHERE file_path = ?", (final_file,)).fetchone()
            self.assertEqual(row["starred"], 1)
            self.assertIn("Verse 2 melody idea", row["notes"])

    def test_running_status_restoration(self):
        start_wall = datetime.now(timezone.utc)
        mono_t = 1000.0

        session = daemon.ActiveSession(
            start_wall_time=start_wall,
            start_mono_time=mono_t,
            device_name="Test Controller",
            sessions_dir=self.sessions_dir,
            journal_dir=self.journal_dir,
        )

        # 1. Full Note-On 0x90
        session.record_event(bytes([0x90, 60, 100]), mono_t)
        # 2. Stripped running status event (only data bytes 62, 90)
        session.record_event(bytes([62, 90]), mono_t + 0.1)

        # Both notes should be registered
        self.assertEqual(session.note_count, 2)
        self.assertIn((0, 60), session.active_notes)
        self.assertIn((0, 62), session.active_notes)
        if session.journal_handle:
            session.journal_handle.close()


class TestCliCommands(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.data_dir = Path(self.temp_dir)
        self.db_path = self.data_dir / "index.db"
        self.db = daemon.DatabaseIndex(self.db_path)
        self.paths = {
            "data_dir": self.data_dir,
            "sessions_dir": self.data_dir / "sessions",
            "journal_dir": self.data_dir / "journal",
            "db_path": self.db_path,
            "pid_file": self.data_dir / "midikeep.pid",
            "config_path": self.data_dir / "config.yaml",
        }

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_cli_star_and_list(self):
        # Insert a session
        fake_file = self.data_dir / "fake.mid"
        fake_file.write_bytes(b"MThd")
        sid = self.db.insert_session(
            start_time="2026-10-05T12:00:00+00:00",
            end_time="2026-10-05T12:05:00+00:00",
            duration_seconds=300.0,
            active_play_seconds=250.0,
            note_count=100,
            device_name="Keystation",
            file_path=str(fake_file),
            key_signature="C Major",
            starred=False,
        )

        # Test starring via CLI handler
        class Args:
            pass

        args = Args()
        args.session_id = sid
        midikeep_cli.cmd_star(args, self.paths)

        with self.db._get_connection() as conn:
            row = conn.execute("SELECT starred FROM sessions WHERE id = ?", (sid,)).fetchone()
            self.assertEqual(row["starred"], 1)

        # Test export
        export_dest = self.data_dir / "exported.mid"
        args.output = str(export_dest)
        midikeep_cli.cmd_export(args, self.paths)
        self.assertTrue(export_dest.exists())
        self.assertEqual(export_dest.read_bytes(), b"MThd")

    def test_cli_mark_with_comment(self):
        class Args:
            pass
        args = Args()
        args.comment = "Awesome guitar solo"
        args.interactive = False
        args.text = None

        with unittest.mock.patch.object(midikeep_cli, "send_daemon_signal", return_value=True):
            midikeep_cli.cmd_mark(args, self.paths)

        marker_file = self.data_dir / "marker.msg"
        self.assertTrue(marker_file.exists())
        self.assertEqual(marker_file.read_text("utf-8"), "Awesome guitar solo")

if __name__ == "__main__":
    unittest.main()
