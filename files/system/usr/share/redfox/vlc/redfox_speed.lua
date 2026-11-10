-- RedFox: R toggles VLC's playback speed, like the browser's video speed
-- controller. At normal speed, R goes to the last other speed used (1.8 to
-- start with); at any other speed, R goes back to normal.
--
-- A VLC Lua interface, loaded at every start by configure-vlc-dewy
-- (extraintf=luaintf, lua-intf=redfox_speed). VLC 3's Lua can't subscribe
-- to key presses, so it checks the last key pressed (libvlc's "key-pressed",
-- which both VLC's window and the video window set) and the speed, 20 times
-- a second. R must not be bound to anything in VLC itself.

local R = string.byte("r")
local NORMAL = 1.0
local last = 1.8 -- the speed R goes to, until another one is used

local libvlc = vlc.object.libvlc()

local function near(a, b) return math.abs(a - b) < 0.005 end

while true do
  local playlist = vlc.object.playlist()
  local rate = vlc.var.get(playlist, "rate") or NORMAL
  if not near(rate, NORMAL) then last = rate end

  if vlc.var.get(libvlc, "key-pressed") == R then
    -- Clear it, so the next R counts too (no key is bound to 0).
    vlc.var.set(libvlc, "key-pressed", 0)
    local new = near(rate, NORMAL) and last or NORMAL
    vlc.var.set(playlist, "rate", new)
    if vlc.object.vout() then
      pcall(vlc.osd.message, string.format("Speed: %.2fx", new), nil, "top-right", 1000000)
    end
  end

  -- VLC interrupts the wait when it closes the interface: then stop.
  if not pcall(vlc.misc.mwait, vlc.misc.mdate() + 50000) then break end
end
