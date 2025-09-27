import { getCurrentInstance } from 'vue';

export default <T = void>(event: string, callback: (data: T) => void) => {
  const root = getCurrentInstance().proxy.$root;

  root.$on(event, callback);
};
