<template>
  <div class="h-full flex flex-col">

    <!-- Header -->
    <header class="px-4 py-2 border-b border-slate-800 bg-slate-900/40 backdrop-blur">
      <h2 class="text-xs font-semibold tracking-wide uppercase">
        Infos & contexte
      </h2>
    </header>

    <!-- Contenu -->
    <div class="flex-1 px-4 py-3 space-y-2 text-xs">

      <p class="opacity-80">
        Ici on affichera :
      </p>

      <ul class="list-disc list-inside space-y-1 opacity-90">
        <li>Modèle sélectionné</li>
        <li>Score de santé des providers</li>
        <li>Historique des décisions de routage</li>
        <li>Contexte de la session</li>
      </ul>

    </div>
  </div>
</template>

<script setup>
</script>

<style scoped>
/* Mode clair */
:global(html.light) header {
  background: rgba(255,255,255,0.6);
  color: #0f172a;
}

:global(html.light) h2,
:global(html.light) p,
:global(html.light) li {
  color: #0f172a;
}
</style>

