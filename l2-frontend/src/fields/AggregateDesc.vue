<template>
  <div class="root-agg">
    <div class="research" v-for="research in data">
      <div class="research-title">{{research.title_research}}</div>
      <div class="research-date" v-for="res in research.result">
        <div class="research-date-title">{{res.date}}:</div>
        <div class="research-group" v-for="g in res.data" v-if="non_empty_group(g)">
          <div class="research-group-title" v-if="g.group_title !== ''">{{g.group_title}}</div>
          <div class="group-field" v-for="f in g.fields">
            <div class="group-field-title" v-if="f.title_field !== ''">{{f.title_field}}:</div>
            <div v-html="fix_html(f.value)"/>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
  import stationar_point from '../api/stationar-point'

  export default {
    props: {
      pk: {},
      extract: {
        type: Boolean,
        default: false
      },
      r_type: {
        type: String,
        required: true,
      },
    },
    data() {
      return {
        data: []
      }
    },
    mounted() {
      this.load()
    },
    methods: {
      async load() {
        this.data = await stationar_point.aggregateDesc(this, ['pk', 'extract', 'r_type'])
      },
      fix_html(v) {
        let lv = v;
        lv = lv.replace('<', '&lt;').replace('>', '&gt;');
        lv.replace('&lt;sub&gt;', '<sub>');
        lv.replace('&lt;/sub&gt;', '</sub>');
        lv.replace('&lt;sup&gt;', '<sup>');
        lv.replace('&lt;/sup&gt;', '</sup>');
        lv = lv.replace('\n', '<br/>');
        return lv;
      },
      non_empty_group(g) {
        if (g.group_title !== '') {
          return true;
        }

        for (const f of g.fields) {
          if (f.value !== '') {
            return true;
          }
        }

        return false;
      }
    },
  }
</script>

<style scoped lang="scss">
  .research-title {
    font-weight: bold;
    font-size: 110%;
  }

  .research-group {
    margin-bottom: 5px;

    &-title {
      font-weight: bold;
    }
  }

  .group-field-title, .research-date-title {
    font-weight: bold;
  }

  .root-agg {
    max-width: 800px;
  }
</style>
