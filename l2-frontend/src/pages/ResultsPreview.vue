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
        <div style="text-align: center;flex-basis: 20%">
          <label><input
            v-model="withSignatureStamps"
            type="checkbox"
          > Штамп ЭЦП</label>
        </div>
        <div style="text-align: center;flex-basis: 20%">
          <label><input
            v-model="split"
            type="checkbox"
          > Отдельные страницы</label>
        </div>
        <div style="text-align: center;flex-basis: 20%">
          <label><input
            v-model="margin"
            type="checkbox"
          > Отступ слева</label>
        </div>
        <div style="text-align: center;flex-basis: 20%">
          <label><input
            v-model="plainProtocolText"
            type="checkbox"
          > Сплошной</label>
        </div>
        <div style="text-align: center;flex-basis: 20%">
          <label><input
            v-model="medCertificate"
            type="checkbox"
          > Справка</label>
        </div>
        <div style="text-align: right;flex-basis: 20%">
          <button
            type="button"
            class="btn btn-blue-nb"
          >
            Обновить
          </button>
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
      split: false,
      margin: false,
      plainProtocolText: false,
      medCertificate: false,
      withSignatureStamps: false,
      pks: [],
      hosp: 0,
      complex: 0,
      portion: 0,
      sort: 0,
    };
  },
  watch: {
    split() {
      localStorage.setItem('print_results_split', String(this.split));
    },
    margin() {
      localStorage.setItem('print_results_margin', String(this.margin));
    },
    plainProtocolText() {
      localStorage.setItem('print_results_protocol_plain_text', String(this.plainProtocolText));
    },
    medCertificate() {
      localStorage.setItem('print_results_med_certificate', String(this.medCertificate));
    },
    withSignatureStamps() {
      localStorage.setItem('print_results_with_signature_stamps', String(this.withSignatureStamps));
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
export default class ResultsPreview extends Vue {
  split: boolean;

  margin: boolean;

  plainProtocolText: boolean;

  medCertificate: boolean;

  withSignatureStamps: boolean;

  pks: number[];

  hosp: number;

  complex: number;

  portion: number;

  sort: number;

  get asVI() {
    return this.$asVI();
  }

  get system() {
    return this.$systemTitle();
  }

  pdfUrlBase() {
    const url = new URL('/results/pdf', window.location.origin);
    url.searchParams.append('pk', JSON.stringify(this.pks));
    url.searchParams.append('split', this.split ? '1' : '0');
    url.searchParams.append('leftnone', this.margin ? '0' : '1');
    url.searchParams.append('protocol_plain_text', this.plainProtocolText ? '1' : '0');
    url.searchParams.append('withSignatureStamps', this.withSignatureStamps ? '1' : '0');
    url.searchParams.append('med_certificate', this.medCertificate ? '1' : '0');
    url.searchParams.append('hosp', String(this.hosp));
    url.searchParams.append('complex', String(this.complex));
    url.searchParams.append('portion', String(this.portion));
    url.searchParams.append('sort', String(this.sort));
    return url;
  }

  get pdfUrlInline() {
    const url = this.pdfUrlBase();
    url.searchParams.append('inline', '1');
    return url.toString();
  }

  get pdfUrlNoInline() {
    const url = this.pdfUrlBase();
    url.searchParams.append('inline', '0');
    return url.toString();
  }

  setParamsFromQuery() {
    const urlParams = new URLSearchParams(window.location.search);
    try {
      this.pks = JSON.parse(urlParams.get('pk') || '[]');
    } catch (e) {
      this.pks = [];
      // eslint-disable-next-line no-console
      console.error(e);
      this.$root.$emit('msg', 'error', 'Ошибка при получении параметров');
    }
    this.hosp = Number(urlParams.get('hosp') || 0);
    this.complex = Number(urlParams.get('complex') || 0);
    this.portion = Number(urlParams.get('portion') || 0);
    this.sort = Number(urlParams.get('sort') || 0);
  }

  loadLocalStorage() {
    this.split = localStorage.getItem('print_results_split') === 'true';
    this.margin = localStorage.getItem('print_results_margin') === 'true';
    this.plainProtocolText = localStorage.getItem('print_results_protocol_plain_text') === 'true';
    this.medCertificate = localStorage.getItem('print_results_med_certificate') === 'true';
    this.withSignatureStamps = localStorage.getItem('print_results_with_signature_stamps') === 'true';
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
