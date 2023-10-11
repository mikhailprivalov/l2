import { getCurrentInstance } from 'vue';

export default () => {
  const root = getCurrentInstance().proxy.$root;

  return {
    error(message: string, timeout: number | void | null) {
      root.$error(message, timeout);
    },
    info(message: string, timeout: number | void | null) {
      root.$info(message, timeout);
    },
    ok(message: string, timeout: number | void | null) {
      root.$ok(message, timeout);
    },
  };
};
