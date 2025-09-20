<script setup lang="ts">
defineProps<{
  icon?: string
  title: string
  details: string
  link?: string
}>()
</script>

<template>
  <div class="VPFeature">
    <article class="box">
      <div class="icon">{{ icon }}</div>
      <h2 class="title">{{ title }}</h2>
      <p class="details" v-html="details"></p>
      <div v-if="link" class="box-footer">
        <a :href="link" class="link">Learn More →</a>
      </div>
    </article>
  </div>
</template>

<style scoped>
.link {
  color: var(--vp-c-brand);
  text-decoration: none;
  font-size: 14px;
  font-weight: 500;
}

.link:hover {
  color: var(--vp-c-brand-dark);
}
</style>
