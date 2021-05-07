<template>
  <tr v-show="ok" :class="{warn: warn, direction: type === 'direction', visit: type === 'visit'}">
    <td>{{researche_title}}</td>
    <td v-if="in_load" colspan="3">поиск результата или назначения...</td>
    <td v-if="!in_load && type === 'result'">
      <a href="#" @click.prevent="show_result">просмотр результата</a>
    </td>
    <td v-if="!in_load && type === 'direction'" colspan="3">
      <a href="#" @click.prevent="show_direction">просмотр направления ({{date}})</a><br/>
      Направление без результата.
      <div v-if="has_last_result">
        <hr style="margin: 5px 0"/>
        <a href="#" @click.prevent="show_result">последний результат ({{last_result.datetime}})</a>
      </div>
    </td>
    <td v-if="!in_load && type === 'visit'" colspan="3">
      {{date}} посещение по направлению без результата.<br/>
      <a href="#" @click.prevent="show_direction">просмотр направления</a>
      <div v-if="has_last_result">
        <hr style="margin: 5px 0"/>
        <a href="#" @click.prevent="show_result">последний результат ({{last_result.datetime}})</a>
      </div>
    </td>
    <td v-if="!in_load && type === 'result'" class="text-center">{{date}}</td>
    <td v-if="!in_load && type === 'result'" class="text-center">
      {{days_str}}
    </td>
  </tr>
</template>

<script>
import moment from 'moment';
import directionsPoint from '../api/directions-point';

moment.updateLocale('ru', {
  relativeTime: {
    s: 'только что',
    m: 'только что',
    mm: '%d мин. назад',
    h: 'час назад',
    hh: '%d ч. назад',
    d: '1 д. назад',
    dd: '%d д. назад',
    M: '1 м. назад',
    MM: '%d м. назад',
    y: '1 г. назад',
    yy: '%d г. назад',
  },
});

export default {
  name: 'last-result',
  props: {
    individual: {
      type: Number,
    },
    research: {
      type: Number,
    },
    parentIss: {
      type: Number,
      default: null,
    },
    noScroll: {
      default: false,
      type: Boolean,
      required: false,
    },
  },
  data() {
    return {
      in_load: true,
      ok: true,
      direction: -1,
      ms: 0,
      days: -1,
      days_str: -1,
      date: '',
      date_orig: '',
      type: 'result',
      last_result: {},
      has_last_result: false,
      is_paraclinic: false,
    };
  },
  mounted() {
    this.load();
  },
  watch: {
    individual() {
      this.load();
    },
  },
  computed: {
    researche_title() {
      for (const pk of Object.keys(this.$store.getters.researches_obj)) {
        const res = this.$store.getters.researches_obj[pk];
        if (res.pk === this.research) {
          return res.title;
        }
      }
      return '';
    },
    warn() {
      return this.days <= 10 && this.ok && !this.in_load;
    },
  },
  methods: {
    show_result() {
      if (this.is_paraclinic) {
        this.$root.$emit('print:results', [this.has_last_result ? this.last_result.direction : this.direction]);
        return;
      }
      this.$root.$emit('show_results', this.direction);
    },
    show_direction() {
      this.$root.$emit('print:directions', [this.direction]);
    },
    load() {
      if (!this.noScroll) {
        window.$('.scrolldown').scrollDown();
      }
      directionsPoint.lastResult(this, ['individual', 'research', 'parentIss']).then((data) => {
        this.in_load = false;
        this.ok = data.ok;
        if (data.ok) {
          this.type = data.type;
          this.date = data.data.datetime;
          if (data.has_last_result) {
            this.last_result = data.last_result;
            this.has_last_result = data.has_last_result;
          }
          this.is_paraclinic = data.data.is_desc;
          const m = moment.unix(data.data.ts);
          const n = moment();
          this.ms = n.diff(m);
          this.days = n.diff(m, 'days');
          this.days_str = moment.duration(this.ms).locale('ru').humanize();
          this.direction = data.data.direction;
        }

        if (!this.noScroll) {
          setTimeout(() => {
            window.$('.scrolldown').scrollDown();
          }, 10);
        }
      });
    },
  },
};
</script>

<style scoped lang="scss">
  td, th {
    padding: 2px !important;
    word-wrap: break-word;
    color: #000
  }

  .warn {
    background-color: #ffa04d;

    &.direction {
      background-color: #ff391a;

      td {
        color: #fff;
      }

      a {
        color: #fff !important;
      }
    }
  }

  .visit {
    background-color: #4dacff;
  }

  :not(.warn) td hr {
    border-top: 1px solid #000;
  }
</style>
