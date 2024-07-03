<template>
  <div v-frag>
    <ul class="nav navbar-nav">
      <li class="dropdown">
        <LaboratorySelector with-forced-update-query />
      </li>
    </ul>
    <ul class="nav navbar-nav">
      <li class="dropdown">
        <div>
          <button
            class="btn btn-blue-nb btn-ell dropdown-toggle bt2"
            type="button"
            data-toggle="dropdown"
          >
            Печатные формы
            <span class="caret" />
          </button>
          <ul
            class="dropdown-menu"
            style="margin-top: 1px"
          >
            <li>
              <ExecutionList />
            </li>
            <li>
              <LaboratoryJournal />
            </li>
            <li>
              <LaboratoryPrintResults />
            </li>
          </ul>
        </div>
      </li>
    </ul>
    <ul class="nav navbar-nav">
      <LoadFile />
    </ul>
  </div>
</template>

<script lang="ts">
import LoadFile from '@/ui-cards/LoadFile.vue';
import LaboratorySelector from '@/ui-cards/LaboratorySelector.vue';
import ExecutionList from '@/ui-cards/ExecutionList.vue';
import LaboratoryJournal from '@/ui-cards/LaboratoryJournal.vue';
import LaboratoryPrintResults from '@/ui-cards/LaboratoryPrintResults.vue';
import UploadFileModal from '@/modals/UploadFileModal.vue';

export default {
  name: 'LaboratoryHeader',
  components: {
    LoadFile,
    LaboratorySelector,
    ExecutionList,
    LaboratoryJournal,
    LaboratoryPrintResults,
  },
  props: {
    withAllLabs: {
      type: Boolean,
      required: false,
      default: false,
    },
  },
};
</script>

<style lang="scss" scoped>
  .bt2 {
      border-radius: 0;
      height: 36px;
      border: none !important;

      &:not(:hover) {
        background-color: #656D78 !important;
      }
  }

  .bt2:hover, .bt2:active, .bt2:focus {
      background: #049372 !important;
      border: none !important;
  }

  .nav-upload-file {
    padding: 8px 15px;
  }

</style>
