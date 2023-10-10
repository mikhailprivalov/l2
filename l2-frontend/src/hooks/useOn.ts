import { getCurrentInstance } from 'vue';

export default (event: string, callback: () => void) => {
  const root = getCurrentInstance().proxy.$root;

  root.$on(event, callback);
};
