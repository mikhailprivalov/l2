const popover = (html: string) => ({
  html,
  arrow: true,
  reactive: true,
  interactive: true,
  animation: 'fade',
  duration: 0,
  theme: 'light',
  placement: 'bottom',
  trigger: 'click',
});

export default popover;
