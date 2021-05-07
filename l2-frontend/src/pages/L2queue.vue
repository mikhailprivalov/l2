<template>
  <div>
    {{name}}
  </div>

</template>

<script>
export default {
  name: 'L2queue',
  data() {
    return {
      name: 'Экраны',
    };
  },
};
</script>

<style>
          body, html {
            height: 100%;
            margin: 0;
        }
        body {
           background: linear-gradient(30deg, rgb(208, 211, 209), rgb(174, 174, 174));
           color: #fff;
           overflow:hidden
           }
        .container-fluid {
            height: 100%;
            width: 100%;
        }

</style>
