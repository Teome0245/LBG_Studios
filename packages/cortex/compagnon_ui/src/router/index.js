import { createRouter, createWebHistory } from "vue-router";
import HomePage from "../pages/HomePage.vue";
import LyraPage from "../pages/LyraPage.vue";
import AgentsMapPage from "../pages/AgentsMapPage.vue";

import ProvidersCatalogPage from "../pages/ProvidersCatalogPage.vue";

const routes = [
  { path: "/", component: HomePage },
  { path: "/lyra", component: LyraPage },
  { path: "/agents/map", component: AgentsMapPage },
  { path: "/providers/catalog", component: ProvidersCatalogPage }
];

export const router = createRouter({
  history: createWebHistory(),
  routes
});
