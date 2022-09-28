// eslint-disable-next-line import/prefer-default-export
export const sendEvent = (event: string, data: any) => {
  // @ts-ignore
  if (window?.posthog) {
    // @ts-ignore
    window.posthog.capture(event, data);
  }
};
