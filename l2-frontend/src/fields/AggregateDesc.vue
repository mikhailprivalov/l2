<template>
  <div class="root-agg">
    <div class="research" v-for="(research, ir) in data" :key="ir">
      <div class="research-title">{{research.title_research}}</div>
      <div v-if="excludedDateDirByGroup(research.title_research).length > 0" class="excluded">
        <u><strong>Исключённые направления:</strong></u>
        <span v-for="t in excludedDateDirByGroup(research.title_research)" :key="t" @click="cancelExcludeDateDir(t)"
              v-tippy="{ placement : 'top', arrow: true }"
              title="Вернуть"
              class="clickable-return">
          {{getAfterGroup(t)}}
        </span>
      </div>
      <!-- eslint-disable-next-line vue/no-use-v-if-with-v-for -->
      <div v-for="(res, i) in research.result" v-if="!excludedDateDir(res.date, research.title_research)"
           :key="i" class="research-date">
        <div
          class="research-date-title"
          @click="excludeDateDir(res.date, research.title_research)"
          title="Скрыть направление"
          v-tippy="{ placement : 'top', arrow: true }"
        >
          {{res.date}}:
        </div>
        <div v-if="res.link_dicom"><a class="a-under" :href="res.link_dicom" target="_blank">снимок</a></div>
        <!-- eslint-disable-next-line vue/no-use-v-if-with-v-for -->
        <span class="research-group" v-for="(g, gi) in res.data" v-if="non_empty_group(g)" :key="gi">
          <span class="research-group-title" v-if="g.group_title !== ''">
            {{fix_space(g.group_title)}}<span v-if="non_empty_fields(g)">:</span></span>
          <!-- eslint-disable-next-line vue/no-use-v-if-with-v-for -->
          <span class="group-field" v-for="(f, fi) in g.fields" v-if="f.value !== ''" :key="fi">
            <span class="group-field-title" v-if="f.title_field !== ''">{{fix_space(f.title_field)}}:&nbsp;</span><span
            v-html="fix_html(f.value)"/><span
            v-if="fi + 1 < g.fields.length && !f.value.endsWith(';') && !f.value.endsWith('.')">; </span><span
            v-else-if="fi + 1 === g.fields.length && !f.value.endsWith(';') && !f.value.endsWith('.')">.</span><span
            v-else>&nbsp;</span>
          </span>
        </span>
      </div>
    </div>
  </div>
</template>

<script>
import stationar_point from '../api/stationar-point';

const delimiter = '#@#';

const makeKey = (t, group) => `${group}${delimiter}${t}`;

export default {
  props: {
    pk: {},
    extract: {
      type: Boolean,
      default: false,
    },
    r_type: {
      type: String,
      required: true,
    },
    value: {},
    disabled: {
      type: Boolean,
      default: false,
    },
  },
  data() {
    return {
      data: [],
      excluded: [],
      inited: false,
    };
  },
  async mounted() {
    await this.load();
    try {
      const valOrig = JSON.parse(this.value || '[]');
      if (Object.prototype.toString.call(valOrig) === '[object Object]' && valOrig.excluded) {
        this.excluded = valOrig.excluded;
      }
    } catch (e) {
      console.log('Aggregate error:', e);
    }
    this.inited = true;
  },
  methods: {
    getAfterGroup(s) {
      return s.split(delimiter)[1];
    },
    async load() {
      this.data = await stationar_point.aggregateDesc(this, ['pk', 'extract', 'r_type']);
    },
    fix_html(v) {
      let lv = v;
      lv = lv.replaceAll('<', '&lt;').replaceAll('>', '&gt;');
      const tagsToRevert = ['sub', 'sup', 'u', 'p', 'strong', 'em'];
      for (const tag of tagsToRevert) {
        lv = lv.replaceAll(`&lt;${tag}&gt;`, `<${tag}>`);
        lv = lv.replaceAll(`&lt;/${tag}&gt;`, `</${tag}>`);
      }
      lv = lv.replaceAll('\n', '<br/>');
      return lv.trim();
    },
    fix_space(v) {
      return v.replace(' ', ' ');
    },
    non_empty_group(g) {
      if (g.group_title !== '') {
        return true;
      }

      return this.non_empty_fields(g);
    },
    non_empty_fields(g) {
      for (const f of g.fields) {
        if (f.value !== '') {
          return true;
        }
      }

      return false;
    },
    excludedDateDirByGroup(group) {
      const title = makeKey('', group);
      return this.excluded.filter((s) => s.startsWith(title));
    },
    cancelExcludeDateDir(title) {
      if (this.disabled) {
        return;
      }
      const pos = this.excluded.findIndex((v) => v === title);
      if (pos === -1) {
        return;
      }
      this.excluded.splice(pos, 1);
    },
    excludeDateDir(t, group) {
      if (this.disabled) {
        return;
      }
      const title = makeKey(t, group);
      if (!this.excluded.includes(title)) {
        this.excluded.push(title);
      }
    },
    excludedDateDir(t, group) {
      const title = makeKey(t, group);
      return this.excluded.includes(title);
    },
  },
  computed: {
    directions() {
      const d = [];
      try {
        if (Array.isArray(this.data)) {
          for (const res of this.data) {
            for (const row of res.result) {
              if (row.date && !this.excludedDateDir(row.date, res.title_research)) {
                d.push(parseInt(row.date.split(' ')[1], 10));
              }
            }
          }
        }
      } catch (e) {
        console.error(e);
      }
      return d;
    },
    val_data() {
      return {
        directions: this.directions,
        excluded: this.excluded,
      };
    },
  },
  watch: {
    val_data: {
      deep: true,
      handler() {
        if (this.inited) {
          this.$emit('input', JSON.stringify(this.val_data));
        }
      },
    },
    inited() {
      if (this.inited) {
        this.$emit('input', JSON.stringify(this.val_data));
      }
    },
  },
};
</script>

<style scoped lang="scss">
  .root-agg {
    line-height: 1.5;
  }

  .research {
    margin-bottom: 10px;

    &-title {
      font-weight: bold;
      font-size: 110%;
    }

    &-date {
      text-align: justify;
    }

    &-group-title {
      font-weight: bold;
    }
  }

  .research-date-title {
    font-weight: bold;
    cursor: pointer;

    &:hover {
      text-decoration: underline;
      background: rgba(#000, .05);
    }
  }

  .root-agg {
    max-width: 21cm;
  }

  .clickable-return {
    cursor: pointer;
    padding: 0 2px;
    border: 1px solid rgba(#049372, .4);
    border-radius: 3px;
    margin-left: 4px;
    margin-bottom: 5px;
    transition: .2s ease-in all;
    white-space: nowrap;
    display: inline-block;

    &:hover {
      color: #fff;
      background: #049372;
      border: 1px solid #049372;
      box-shadow: 0 7px 14px #04937254, 0 5px 5px #049372ba;
    }
  }

  .excluded {
    white-space: normal;
    word-break: break-word;
  }
</style>
