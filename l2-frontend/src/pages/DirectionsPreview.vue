<template>
  <div class="root-container">
    <div class="results-header">
      <div class="header-inner">
        <div class="system-logo">
          <template v-if="asVI">
            {{ system }}
          </template>
          <template v-else>
            L<sup>2</sup>
          </template>
        </div>
        <div style="text-align: center;flex-basis: 100%">
          <label><input
            v-model="narrowFormat"
            type="checkbox"
          > 80 мм </label>
        </div>
      </div>
    </div>
    <div class="pdf-root">
      <div
        ref="pdf"
        class="pdf-inner"
      />
    </div>
  </div>
</template>

<script lang="ts">
import Vue from 'vue';
import Component from 'vue-class-component';
import PDFObject from 'pdfobject';

@Component({
  data() {
    return {
      narrowFormat: false,
      pks: [],
    };
  },
  watch: {
    narrowFormat() {
      localStorage.setItem('direction_narrow_format', String(this.narrowFormat));
    },
    pdfUrlInline() {
      PDFObject.embed(this.pdfUrlInline, this.$refs.pdf, {
        fallbackLink: `<p>Невозможно отобразить PDF. <a href='${this.pdfUrlNoInline}'>Скачать файл</a></p>`,
      });
    },
  },
  mounted() {
    this.setParamsFromQuery();
    this.loadLocalStorage();
    window.addEventListener('keydown', this.keyHandler);
  },
  beforeDestroy() {
    window.removeEventListener('keydown', this.keyHandler);
  },
})
export default class DirectionsPreview extends Vue {
  narrowFormat: boolean;

  pks: number[];

  get asVI() {
    return this.$asVI();
  }

  get system() {
    return this.$systemTitle();
  }

  pdfUrlBase() {
    const url = new URL('/directions/pdf', window.location.origin);
    url.searchParams.append('napr_id', JSON.stringify(this.pks));
    url.searchParams.append('narrowFormat', this.narrowFormat ? '1' : '0');
    return url;
  }

  get pdfUrlNoInline() {
    const url = this.pdfUrlBase();
    return url.toString();
  }

  get pdfUrlInline() {
    const url = this.pdfUrlBase();
    url.searchParams.append('inline', '1');
    return url.toString();
  }

  setParamsFromQuery() {
    const urlParams = new URLSearchParams(window.location.search);
    try {
      this.pks = JSON.parse(urlParams.get('napr_id') || '[]');
    } catch (e) {
      this.pks = [];
      // eslint-disable-next-line no-console
      console.error(e);
      this.$root.$emit('msg', 'error', 'Ошибка при получении параметров');
    }
  }

  loadLocalStorage() {
    this.narrowFormat = localStorage.getItem('direction_narrow_format') === 'true';
  }

  keyHandler(event) {
    if (event.ctrlKey || event.metaKey) {
      if (String.fromCharCode(event.which).toLowerCase() === 's') {
        event.preventDefault();
        window.open(this.pdfUrlNoInline, '_blank');
      }
    }
  }
}
</script>

<style scoped lang="scss">
.root-container {
  display: flex;
  flex-direction: column;
  margin: 0;
  padding: 0;
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  overflow: hidden;
}

.results-header {
  flex: 0 0 48px;
  background-color: rgb(50, 54, 57);
  color: #fff;
  border-bottom: 1px solid #049372;
  padding-left: 17px;
  padding-right: 17px;
}

.header-inner {
  height: 100%;
  width: 100%;
  display: flex;
  flex-direction: row;
  justify-content: space-between;
  align-items: center;
}

.system-logo {
    font-weight: 500;
    font-style: italic;
    font-size: 32px;
    flex-basis: 15%
}

.system-logo sup {
    font-size: 17px;
    top: -.15em;
}

.pdf-root {
  flex: 1;
}

.pdf-inner {
  height: 100%;
}
</style>
