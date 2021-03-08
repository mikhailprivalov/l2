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
      <i class="fa fa-vials"></i>
    </a>

    <div id="favorites-view" class="tp">
      <table class="table">
        <colgroup>
          <col width='40'/>
          <col width='100'/>
          <col width='300'/>
          <col width='20'/>
        </colgroup>
        <tbody>
        <tr>
          <td>
          </td>
          <td>
            <a href="#" @click.prevent="minus_year"><i class="fa fa-angle-double-left"></i></a>
            <a href="#">{{ current_year }}</a>
            <a href="#" @click.prevent="plus_year"><i class="fa fa-angle-double-right"></i></a>
            <a href="#" @click.prevent="set_current_year" style="padding-left: 5px"><i class="fa fa-circle"></i></a>
          </td>
          <td>
          </td>
          <td>
          </td>
        </tr>
        <tr  v-for="row in data">
          <td>
            <a href="#" @click.prevent="load">{{row.dir}}</a>
          </td>
          <td>
            <a href="#" @click.prevent="load">{{row.date}}</a>
          </td>
          <td>
            <a href="#" @click.prevent="load">{{row.reserches}}</a>
          </td>
          <td class="nopd"><input type="checkbox"/></td>
        </tr>
        </tbody>
      </table>
    </div>
  </fragment>
</template>

<script>
  import api from '@/api'
  import moment from "moment";

  export default {
    name: "ResultsLaboratory",
    props: {
      card_pk: {
        type: Number,
        required: true,
      }
    },
    data() {
      return {
        data: '',
        current_year: moment().format('YYYY'),
        is_lab: true,

      }
    },
    mounted() {
      this.load();
      console.log(this.year)
    },
    methods: {
      async load() {
        const result = await api('directions/result-patient-year', this,['card_pk','current_year', 'is_lab']);
        this.data = [...result.results]
        console.log(this.data)
      },
      print_med_certificate(type_form, direction) {
        window.open(`/medical_certificates/pdf?type=${type_form}&dir=${direction}`, '_blank')
      },
      plus_year() {
        this.current_year = moment(this.current_year).add(1, 'year').format('YYYY');
      },
      minus_year() {
        this.current_year = moment(this.current_year).subtract(1, 'year').format('YYYY');
      },
      set_current_year() {
        this.current_year = moment().format('YYYY')
        this.load()
      }
    },
  }
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
