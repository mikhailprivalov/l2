<template>
  <fragment>
    <a href="#" class="dropdown-toggle" style="color: #049372" @click.prevent
       v-tippy="{
                html: '#favorites-view',
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
             }">
        Справки
    </a>

    <div id="favorites-view" class="tp">
      <table class="table table-condensed table-bordered">
        <tbody>
        <tr v-for="row in data" :class="{'cancel-row': row.cancel}">
          <td>
            <a href="#" @click.prevent="edit_data(row)">{{row}} <i class="fa fa-print"/></a>
          </td>
        </tr>
        </tbody>
      </table>
    </div>
  </fragment>
</template>

<script>

  export default {
    name: "Certificates",
    data() {
      return {
        data: ['Бассейн', 'О проведенном приеме'],
      }
    },
    methods: {

    },
  }
</script>

<style scoped lang="scss">
  .cancel-row {
    td, th {
      opacity: .6;
      text-decoration: line-through;
    }

    &:hover {
      td, th {
        opacity: 1;
        text-decoration: none;
      }
    }
  }

  .size-btn {
    width: 50px;
  }

  .fv {
    cursor: pointer;

    &:hover span {
      text-shadow: 0 0 3px rgba(#049372, .4);
      color: #049372;
    }
  }

  i {
    vertical-align: middle;
    display: inline-block;
    margin-right: 3px;
  }

  .inFavorite i {
    color: #93046d;
  }

  .tp {
    text-align: left;
    line-height: 1.1;
    padding: 5px;

    table {
      margin: 0;
    }

    max-height: 600px;
    overflow-y: auto;
  }
</style>
