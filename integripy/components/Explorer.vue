<template>
<div>
  <b-row>
    <b-col v-if="!source" class="col-1 d-flex justify-content-center">
      <b-button @click="transfer()" :disabled="!dstToSrc.length" variant="primary">
        <font-awesome-icon :icon="['fas', 'angle-left']" />
      </b-button>
    </b-col>
    <b-col class="col-11">
      <div class="d-flex justify-content-between align-items-center">
        <span class="font-weight-bold">Disk Space</span>
        <div>
          <span :class="{ 'text-success': transferSize }">{{ usedSizeHuman }}</span> / <span>{{ totalSizeHuman }}</span>
        </div>
      </div>
      <b-progress :max="explorer.total_size">
        <b-progress-bar :value="explorer.total_size - explorer.free_size" variant="primary"></b-progress-bar>
        <b-progress-bar :value="transferSize" :variant="[usedSize > explorer.total_size ? 'danger' : 'success']"></b-progress-bar>
      </b-progress>
      <b-button-group class="breadcrumb">
        <b-button v-for="(part, index) in explorer.parts" :key="index" @click="explore(joinParts(part))">
          {{ part }}
        </b-button>
      </b-button-group>
      <b-list-group>
        <b-list-group-item v-for="(child, index) in explorer.children" :key="index" :variant="child.corrupt ? 'danger' : ''">
          <div class="d-flex justify-content-between align-items-center">
            <div class="d-flex justify-content-start align-items-center">
              <b-form-checkbox v-model="child.selected" :disabled="child.corrupt || childSize(child) == 0" @input="updateTransferChildren(child)"></b-form-checkbox>
              <div :class="{ 'computing': child.computing }">
                <span v-if="child.directory" @click="explore(child.path)" class="directory">
                  {{ child.name }}
                </span>
                <span v-else v-b-tooltip.hover :title="child.clean_hash">{{ child.name }}</span>
                <span v-if="childSize(child)" class="text-muted">&nbsp;{{ childSizeHuman(child) }}</span>
              </div>
            </div>
            <b-button-group v-if="!child.directory">
              <b-button v-b-tooltip.hover title="Check Integrity" size="sm" variant="primary" @click="checkIntegrity(child)">
                <font-awesome-icon :icon="['fas', 'check']" />
              </b-button>
              <b-button v-b-tooltip.hover title="Update Hash File" size="sm" variant="primary" @click="updateHashFile(child)">
                <font-awesome-icon :icon="['fas', 'sync-alt']" />
              </b-button>
            </b-button-group>
          </div>
        </b-list-group-item>
      </b-list-group>
    </b-col>
    <b-col v-if="source" class="col-1 d-flex justify-content-center">
      <b-button @click="transfer()" :disabled="!srcToDst.length" variant="primary">
        <font-awesome-icon :icon="['fas', 'angle-right']" />
      </b-button>
    </b-col>
  </b-row>

</div>
</template>

<script>
import axios from 'axios'
import filesize from 'filesize'

import EventBus from '../event-bus.js'

export default {
  name: 'explorer',
  data() {
    return {
      explorer: {
        free_size: 0,
        total_size: 0
      }
    }
  },
  props: {
    source: Boolean,
    srcToDst: Array,
    dstToSrc: Array
  },
  computed: {
    usedSize() {
      return this.explorer.total_size - this.explorer.free_size + this.transferSize;
    },
    usedSizeHuman() {
      return filesize(this.usedSize);
    },
    totalSizeHuman() {
      return filesize(this.explorer.total_size);
    },
    transferSize() {
      if (this.source) {
        return this.dstToSrc.map(child => child.dst_size - child.src_size).reduce((a, b) => a + b, 0);
      } else {
        return this.srcToDst.map(child => child.src_size - child.dst_size).reduce((a, b) => a + b, 0);
      }
    }
  },
  methods: {
    joinParts: function(part) {
      return this.explorer.parts.slice(1, this.explorer.parts.indexOf(part) + 1).join('/');
    },
    childSize: function(child) {
      return this.source ? child.src_size : child.dst_size;
    },
    childSizeHuman: function(child) {
      return filesize(this.childSize(child));
    },
    explore: function(path) {
      axios.post('explorer', {
          path: path,
          src: this.source
        })
        .then(response => {
          this.explorer = response.data;
          this.explorer.children
            .filter((child) => !child.directory)
            .forEach((child) => {
              this.fileSize(child);
            });
          this.explorer.children
            .filter((child) => child.directory && child.name != '.' && child.name != '..')
            .forEach((child) => {
              this.directorySize(child);
            });
        });
    },
    directorySize: function(child) {
      axios.post('directory_size', {
          path: child.path,
          src: this.source
        })
        .then(response => {
          child.src_size = response.data.src_size;
          child.dst_size = response.data.dst_size;
        });
    },
    fileSize: function(child) {
      axios.post('file_size', {
          path: child.path,
          src: this.source
        })
        .then(response => {
          child.src_size = response.data.src_size;
          child.dst_size = response.data.dst_size;
        });
    },
    transfer: function() {
      var arr = this.source ? this.srcToDst : this.dstToSrc;
      arr.forEach((child) => {
        child.computing = true;
        axios.post('transfer', {
            path: child.path,
            src: this.source
          })
          .then(response => {
            child.computing = false;
            child.selected = false;
            EventBus.$emit('transferred');
          });
      });
    },
    checkIntegrity: function(child) {
      child.computing = true;
      axios.post('check_integrity', {
          path: child.path,
          src: this.source
        })
        .then(response => {
          child.corrupt = response.data;
          child.computing = false;
        });
    },
    updateHashFile: function(child) {
      child.computing = true;
      axios.post('update_hash_file', {
          path: child.path,
          src: this.source
        })
        .then(response => {
          child.computing = false;
          this.explore(this.explorer.path);
        });
    },
    updateTransferChildren: function(child) {
      var arr = this.source ? this.srcToDst : this.dstToSrc;
      arr.filter((item) => item.path == child.path).forEach((item) => {
        arr.splice(arr.indexOf(item), 1);
      });
      if (child.selected) {
        arr.push(child);
      }
    }
  },
  mounted() {
    EventBus.$on('transferred', () => {
      this.explore(this.explorer.path);
    });
    this.explore('');
  }
}
</script>

<style>
.breadcrumb {
  margin-top: 1em;
  margin-bottom: 1em;
}

.directory {
  font-weight: bold;
  cursor: pointer
}

@keyframes pulse {
  0% {
    opacity: 1.0;
  }
  50% {
    opacity: 0.0;
  }
  100% {
    opacity: 1.0;
  }
}

.computing {
  animation: pulse 2s ease-out;
  animation-iteration-count: infinite;
  opacity: 1;
}
</style>
