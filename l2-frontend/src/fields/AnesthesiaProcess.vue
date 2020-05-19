<template>
  <div>
   <table width="100%" cellspacing="0" border="1">
     <tr>
      <th>SpO2</th>
      <th>10:05</th>
      <th>10:15</th>
      <th>10:25</th>
      <th>10:35</th>
      <th>10:45</th>
      <th>10:55</th>
      <th>11:05</th>
      <th>11:15</th>
      <th>11:25</th>
      <th>11:35</th>
      <th>11:45</th>
      <th>11:55</th>
      <th>12:05</th>
      <th>12:15</th>
      <th>12:25</th>
      <th>12:35</th>
      <th>12:45</th>
      <th>12:55</th>
      <th>13:05</th>
      <th>13:15</th>
     </tr>
     <tr>
      <th>CО2</th>
      <td>5.5</td>
      <td>6.0</td>
      <td>7.0</td>
      <td>7.0</td>
      <td>8.0</td>
      <td>9.0</td>
      <td>1.0</td>
      <td>2.0</td>
     </tr>
     <tr>
      <th>Температура</th>
      <td>Да</td>
      <td>Да</td>
      <td>Да</td>
      <td>Да</td>
      <td>Да</td>
      <td>Да</td>
      <td>Да</td>
      <td>Да</td>
     </tr>
     <tr>
      <th>САД</th>
      <td>Да</td>
      <td>Да</td>
      <td>Да</td>
      <td>Да</td>
      <td>Да</td>
      <td>Да</td>
      <td>Да</td>
      <td>Да</td>
     </tr>
     <tr>
     <th>ДАД</th>
      <td>Да</td>
      <td>Да</td>
      <td>Да</td>
      <td>Да</td>
      <td>Да</td>
      <td>Да</td>
      <td>Да</td>
      <td>Да</td>
     </tr>
    </table>
  </div>

</template>

<script>
    export default {
        name: "AnesthesiaProcess"
    }
</script>

<style scoped>
  table {
     border-collapse: collapse; /* Отображать двойные линии как одинарные */
    }
    th {
     background: #ccc; /* Цвет фона */
     text-align: left; /* Выравнивание по левому краю */
    }
    td, th {
     border: 1px solid #800; /* Параметры границы */
     padding: 4px; /* Поля в ячейках */
    }

</style>
