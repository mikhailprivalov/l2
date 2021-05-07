<template>
  <div class="root-dd"
       v-tippy="{
                html: '#tp-' + direction.pk,
                reactive: true,
                arrow: true,
                animation: 'fade',
                duration: 0,
                theme: 'light',
                placement: 'bottom',
                popperOptions: {
                  modifiers: {
                    preventOverflow: {
                      boundariesElement: 'window'
                    },
                    hide: {
                      enabled: false
                    }
                  }
                },
             }">
    <div class="date">
      {{direction.date_create}}
    </div>
    <div class="dep" v-if="Boolean(direction.podrazdeleniye) && direction.researches.length !== 1">
      {{direction.podrazdeleniye}}
    </div>
    <div class="dep" v-else>
      {{direction.researches_short[0] || direction.researches[0]}}
    </div>

    <div :id="`tp-${direction.pk}`" class="tp">
      <div class="t-left">
        <div>№ {{direction.pk}}</div>
        <div>{{direction.date_create}}</div>
      </div>
      <div class="t-right">
        <ul>
          <li><strong>Назначения:</strong></li>
          <li v-for="r in direction.researches" :key="r">{{r}}</li>
        </ul>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'DisplayDirection',
  props: ['direction'],
};
</script>

<style scoped lang="scss">
  .root-dd {
    padding: 3px;
    text-align: left;
    width: 100%;
    height: 100%;
    font-size: 12px;
  }

  .dep {
    white-space: nowrap;
    text-overflow: ellipsis;
    overflow: hidden;
  }

  .tp {
    text-align: left;
    line-height: 1.1;
    font-size: 14px;

    ul {
      padding-left: 20px;
      margin: 0;
    }
  }

  .t-left {
    width: 100px
  }

  .t-right {
    max-width: 300px;
  }

  .t-left, .t-right {
    display: inline-block;
    vertical-align: top;
  }
</style>
