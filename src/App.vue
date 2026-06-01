<template>
  <main class="app-shell">
    <section class="workspace">
      <p class="kicker">Vue + Vite</p>
      <h1>AC Recommender</h1>
      <p class="summary">A small frontend shell is ready for this recommendation workspace.</p>

      <div class="status-grid" aria-label="Workspace areas">
        <article v-for="item in areas" :key="item.name" class="status-item">
          <span>{{ item.name }}</span>
          <strong>{{ item.path }}</strong>
        </article>
      </div>
    </section>
  </main>
</template>

<script setup>
const areas = [
  { name: 'IR docs', path: 'docs/ir' },
  { name: 'Schema', path: 'schema' },
  { name: 'Scripts', path: 'scripts' },
  { name: 'Taxonomies', path: 'taxonomies' },
]
</script>
