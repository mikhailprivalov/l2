<template>
  <ul class="nav navbar-nav">
    <li
      v-for="list in lists"
      :key="list.cases ? 'cases' : 'documents'"
      class="dropdown"
    >
      <a
        v-tippy="{
          html: `#${list.tipId}`,
          reactive: true,
          interactive: true,
          arrow: true,
          animation: 'fade',
          duration: 0,
          theme: 'light',
          placement: 'bottom',
          trigger: 'click mouseenter',
          popperOptions: {
            modifiers: {
              preventOverflow: {
                boundariesElement: 'window',
              },
              hide: {
                enabled: false,
              },
            },
          },
        }"
        href="#"
        class="dropdown-toggle"
        @click.prevent
      >
        {{ list.title }} <span class="badge badge-light">{{ list.rows.length }}</span>
      </a>
      <div
        :id="list.tipId"
        class="tp"
      >
        <table class="table table-condensed table-bordered">
          <tbody>
            <tr
              v-for="row in list.rows"
              :key="row.id"
            >
              <td>
                <a
                  href="#"
                  @click.prevent="openRow(row.id, list.cases)"
                >{{ row.title }}</a>
              </td>
              <td>
                <button
                  class="favorite-star favorite-star--on"
                  type="button"
                  title="Убрать из избранного"
                  @click="removeRow(row.id, list.cases)"
                >
                  <i class="fa fa-star" />
                </button>
              </td>
            </tr>
          </tbody>
        </table>
        <div v-if="list.rows.length === 0">
          {{ list.empty }}
        </div>
      </div>
    </li>
  </ul>
</template>

<script lang="ts">
import api from '@/api';

export default {
  name: 'DouDocumentFavorites',
  data() {
    return {
      documents: [],
      cases: [],
    };
  },
  computed: {
    lists() {
      return [
        {
          cases: false,
          title: 'Избранные документы',
          empty: 'Нет избранных документов',
          tipId: 'dou-favorite-documents',
          rows: this.documents,
        },
        {
          cases: true,
          title: 'Избранные дела',
          empty: 'Нет избранных дел',
          tipId: 'dou-favorite-cases',
          rows: this.cases,
        },
      ];
    },
  },
  mounted() {
    this.load();
    this.$root.$on('dou-favorites-changed', this.load);
  },
  beforeUnmount() {
    this.$root.$off('dou-favorites-changed', this.load);
  },
  methods: {
    async load() {
      const [documents, cases] = await Promise.all([
        api('document-manager/record-favorites/list', { cases: false }),
        api('document-manager/record-favorites/list', { cases: true }),
      ]);
      this.documents = documents?.result || [];
      this.cases = cases?.result || [];
    },
    openRow(id, cases) {
      this.$root.$emit('open-dou-document', { id, cases: Boolean(cases) });
    },
    async removeRow(id, cases) {
      const result = await api('document-manager/record-favorites/toggle', { id, case: Boolean(cases) });
      if (result?.ok) {
        this.$root.$emit('dou-favorites-changed', { id, favorite: result.favorite, case: Boolean(cases) });
      }
    },
  },
};
</script>

<style scoped lang="scss">
.tp {
  text-align: left;
  line-height: 1.1;
  padding: 5px;
  max-height: 600px;
  overflow-y: auto;

  table {
    margin: 0;
  }
}

.favorite-star {
  border: none;
  background: transparent;
  padding: 0 4px;
  cursor: pointer;
  color: #aab2bd;
}

.favorite-star--on {
  color: #93046d;
}
</style>
