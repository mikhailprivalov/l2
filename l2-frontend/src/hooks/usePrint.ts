import { getCurrentInstance } from 'vue';

export default () => {
  const root = getCurrentInstance().proxy.$root;

  return {
    printResults(ids: number[]) {
      root.$emit(
        'print:results',
        ids,
      );
    },
  };
};
