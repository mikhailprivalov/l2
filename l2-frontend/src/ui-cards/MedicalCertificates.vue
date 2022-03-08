<template>
  <div v-frag>
    <a
      v-if="is_med_certificates"
      v-tippy="{
        html: '#certificates-view',
        reactive: true,
        interactive: true,
        arrow: true,
        animation: 'fade',
        duration: 0,
        theme: 'light',
        placement: 'bottom',
        trigger: 'click mouseenter',
        zIndex: 4999,
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
      href="#"
      class="dropdown-toggle"
      style="color: #049372"
      @click.prevent
    >
      Справки
    </a>

    <div
      v-if="is_med_certificates"
      id="certificates-view"
      class="tp"
    >
      <table class="table">
        <tbody>
          <tr
            v-for="row in med_certificates"
            :key="`${row.form}_${row.title}`"
          >
            <td>
              <a
                href="#"
                @click.prevent="print_med_certificate(row.form, direction)"
              >{{ row.title }} <i class="fa fa-print" /></a>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script lang="ts">
export default {
  name: 'Certificates',
  props: {
    med_certificates: {
      type: Array,
      required: false,
    },
    direction: {
      type: Number,
      required: false,
    },
  },
  computed: {
    is_med_certificates() {
      return this.med_certificates.length > 0;
    },
  },
  methods: {
    print_med_certificate(type_form, direction) {
      window.open(`/medical_certificates/pdf?type=${type_form}&dir=${direction}`, '_blank');
    },
  },
};
</script>

<style scoped lang="scss">

  i {
    vertical-align: middle;
    display: inline-block;
    margin-right: 3px;
  }

  .tp {
    text-align: left;
    padding: 1px;

    table {
      margin: 0;
    }

    max-height: 600px;
    overflow-y: auto;
  }
</style>
