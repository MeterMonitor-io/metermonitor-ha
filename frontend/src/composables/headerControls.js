import { inject } from 'vue';

export const headerControlsKey = Symbol('headerControls');

export const useHeaderControls = () => inject(headerControlsKey, null);
