export function enter_field(skip) {
  if (!skip) {
    return () => {
    }
  }
  return $e => {
    this.prev_scroll = $('.results-editor').scrollTop();
    const {offsetHeight: oh, scrollHeight: sh} = $('.results-editor')[0];
    this.prev_scrollHeightTop = sh - oh;
    const $elem = $($e.target);
    $elem.addClass('open-field')
  }
}

export function leave_field(skip) {
  if (!skip) {
    return () => {
    }
  }
  return $e => {
    const {offsetHeight: oh, scrollHeight: sh} = $('.results-editor > div')[0];
    if (sh > oh && this.prev_scrollHeightTop < $('.results-editor').scrollTop())
      $('.results-editor').scrollTo(this.prev_scroll).scrollLeft(0);
    let $elem = $($e.target);
    $elem.removeClass('open-field')
  }
}
