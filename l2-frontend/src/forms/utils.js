export function enter_field(skip) {
  if (!skip) {
    return () => {
      // pass
    };
  }
  return ($e) => {
    this.prev_scroll = window.$('.results-editor').scrollTop();
    const { offsetHeight: oh, scrollHeight: sh } = window.$('.results-editor')[0];
    this.prev_scrollHeightTop = sh - oh;
    const $elem = window.$($e.target);
    $elem.addClass('open-field');
  };
}

export function leave_field(skip) {
  if (!skip) {
    return () => {
      // pass
    };
  }
  return ($e) => {
    const { offsetHeight: oh, scrollHeight: sh } = window.$('.results-editor > div')[0];
    if (sh > oh && this.prev_scrollHeightTop < window.$('.results-editor').scrollTop()) {
      window.$('.results-editor').scrollTo(this.prev_scroll).scrollLeft(0);
    }
    const $elem = window.$($e.target);
    $elem.removeClass('open-field');
  };
}
