// Reply, Reply all and Forward in the message pane's header bar, the way GNOME
// mail apps have them, through Mailspring's own toolbar slot for plugins
// ("ThreadActionsToolbarButton", the one archive and trash use). The buttons
// call the same actions as Mailspring's keyboard shortcuts.
// Plugins get React from mailspring-exports; a plain require('react') doesn't
// resolve from a user package.
const { React, Actions, localized } = require('mailspring-exports');
const { RetinaImg } = require('mailspring-component-kit');

const h = React.createElement;

function button(title, image, onClick) {
  return h('button', { className: 'btn btn-toolbar redfox-reply-button', title, onClick },
    h(RetinaImg, { name: image, mode: RetinaImg.Mode.ContentIsMask }));
}

function RedFoxReplyButtons(props) {
  const threads = props.items || [];
  if (threads.length !== 1) return null;
  const thread = threads[0];
  return h('div', { className: 'button-group redfox-reply-buttons' },
    button(localized('Reply'), 'toolbar-reply.png',
      () => Actions.composeReply({ thread, type: 'reply', behavior: 'prefer-existing' })),
    button(localized('Reply All'), 'toolbar-reply-all.png',
      () => Actions.composeReply({ thread, type: 'reply-all', behavior: 'prefer-existing' })),
    button(localized('Forward'), 'toolbar-forward.png',
      () => Actions.composeForward({ thread })));
}
RedFoxReplyButtons.displayName = 'RedFoxReplyButtons';
RedFoxReplyButtons.containerRequired = false;

module.exports = RedFoxReplyButtons;
