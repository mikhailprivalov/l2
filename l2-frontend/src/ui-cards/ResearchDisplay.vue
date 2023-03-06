<template>
  <div
    v-tippy="no_tooltip ? null : {html: '#research-display-' + pk, reactive: true, interactive: true, theme: 'light',
                                  arrow: true,
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
    }"
    class="root-c"
    @click.left="update_comment"
    @click.right.prevent="update_comment"
  >
    <div class="root-in">
      <span
        v-if="category"
        class="category"
      >[{{ category }}]</span>
      {{ title }}
      <span
        v-if="count > 1"
        class="count"
      >(x{{ count }})</span>
      <span
        v-if="comment !== '' && !simple"
        class="comment"
      >[{{ comment }}]</span>
      <span
        v-if="service_location !== '' && !simple"
        class="service_location"
      >[{{ service_location }}]</span>
      <span
        v-if="has_not_filled && !simple"
        class="has_not_filled"
      >[параметры не заполнены]</span>
      <span
        v-else-if="has_params && !simple"
        class="has_params"
      >[параметры]</span>
    </div>
    <div
      v-if="n + 1 < nof"
      class="root-div"
    />
    <div
      v-if="!no_tooltip"
      :id="`research-display-${pk}`"
      class="tp"
    >
      <div style="text-align: left">
        <div class="param">
          <strong>Назначение:</strong> {{ title }}
        </div>
        <div class="param">
          <strong>Количество:</strong> {{ count }}
        </div>
        <button
          v-if="!simple && !readonly"
          class="btn btn-blue-nb btn-sm"
          @click.stop="update_comment"
        >
          Настройка
        </button>
        <button
          v-if="!readonly"
          class="btn btn-blue-nb btn-sm"
          @click.stop="remove"
        >
          Убрать
        </button>
        <div v-if="has_not_filled && !simple">
          <div><strong>Незаполненные поля:</strong></div>
          <ul>
            <li
              v-for="f in not_filled_fields"
              :key="f"
            >
              {{ f }}
            </li>
          </ul>
        </div>
      </div>
    </div>
  </div>
</template>

<script lang="ts">
export default {
  name: 'ResearchDisplay',
  props: {
    title: {
      type: String,
    },
    n: {
      type: Number,
    },
    nof: {
      type: Number,
    },
    pk: {
      type: Number,
    },
    comment: {
      type: String,
      default: '',
    },
    kk: {
      type: String,
      default: '',
    },
    service_location: {
      type: String,
      default: '',
    },
    simple: {
      type: Boolean,
      default: false,
    },
    readonly: {
      type: Boolean,
      default: false,
    },
    no_tooltip: {
      type: Boolean,
      default: false,
    },
    has_not_filled: {
      type: Boolean,
      default: false,
    },
    has_params: {
      type: Boolean,
      default: false,
    },
    count: {
      type: Number,
      default: 1,
    },
    category: {
      type: String,
    },
    not_filled_fields: {
      type: Array,
    },
  },
  methods: {
    remove() {
      this.$root.$emit(`researches-picker:deselect${this.kk}`, this.pk);
    },
    update_comment() {
      if (this.simple) return;
      this.$root.$emit(`researches-picker:update-comment${this.kk}`, this.pk);
    },
  },
};
</script>

<style scoped>
.root-c {
  display: inline-block;
  white-space: nowrap;
  max-width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
}

.root-in, .root-div {
  display: inline-block;
}

.root-in {
  padding: 3px;
  cursor: pointer;
  border: 1px solid transparent;
  font-size: 12px;
}

.root-in:hover {
  background-color: #eee;
  border-color: #bbb;
}

.root-div {
  width: 1px;
  height: 15px;
  background-color: #000;
  margin-bottom: -3px;
  margin-left: -1px;
  margin-right: 3px;
}

.comment {
  margin-left: 3px;
  color: #049372;
  font-weight: 600;
}

.count {
  margin-left: 3px;
  color: #932a04;
  font-weight: 600;
}

.service_location {
  margin-left: 3px;
  color: #93046d;
  font-weight: 600;
}

.has_not_filled {
  margin-left: 3px;
  color: #a00;
  font-weight: 600;
}

.has_params {
  margin-left: 3px;
  color: #0ab;
  font-weight: 600;
}

.category {
  margin-right: 3px;
  color: #042693;
  font-weight: 600;
}
</style>
