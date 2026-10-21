export function enterField(skip = false) {
  if (!skip) {
    return () => {
      // pass
    };
  }
  return ($e) => {
    const editor = window.$('.results-editor')[0];
    if (editor) {
      this.prev_scroll = window.$('.results-editor').scrollTop();
      const { offsetHeight: oh, scrollHeight: sh } = editor;
      this.prev_scrollHeightTop = sh - oh;
    }
    const $elem = window.$($e.target);
    $elem.addClass('open-field');
  };
}

export function leaveField(skip = false) {
  if (!skip) {
    return () => {
      // pass
    };
  }
  return ($e) => {
    const editor = window.$('.results-editor > div')[0];
    if (editor) {
      const { offsetHeight: oh, scrollHeight: sh } = editor;
      if (sh > oh && this.prev_scrollHeightTop < window.$('.results-editor').scrollTop()) {
        window.$('.results-editor').scrollTo(this.prev_scroll).scrollLeft(0);
      }
    }
    const $elem = window.$($e.target);
    $elem.removeClass('open-field');
  };
}
