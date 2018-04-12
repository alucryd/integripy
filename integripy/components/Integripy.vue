<template>
<div id="integripy">
  <b-jumbotron header="Integripy">
    <br />
    <b-card-group deck>
      <b-card title="Current">
        <explorer :source="true" :srcToDst="srcToDst" :dstToSrc="dstToSrc" />
      </b-card>
      <b-card title="Backup">
        <explorer :source="false" :srcToDst="srcToDst" :dstToSrc="dstToSrc" />
      </b-card>
    </b-card-group>
  </b-jumbotron>
</div>
</template>

<script>
export default {
  name: 'integripy',
  data() {
    return {
      srcToDst: [],
      dstToSrc: []
    }
  }
}
</script>

<style>
</style>
