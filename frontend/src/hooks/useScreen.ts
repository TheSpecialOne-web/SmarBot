import { useMediaQuery } from "@mui/material";

import { MOBILE_WIDTH, TABLET_WIDTH } from "@/const";

export const useScreen = () => {
  const isMobile = useMediaQuery(`(max-width:${MOBILE_WIDTH}px)`);
  const isTablet = useMediaQuery(`(max-width:${TABLET_WIDTH}px)`);
  const isDesktop = useMediaQuery(`(min-width:${TABLET_WIDTH}px)`);

  return { isMobile, isTablet, isDesktop };
};
