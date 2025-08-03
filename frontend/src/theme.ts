import { blue, grey, red } from "@mui/material/colors";
import { createTheme } from "@mui/material/styles";

declare module "@mui/material/Typography" {
  interface TypographyPropsVariantOverrides {
    body3: true;
    body4: true;
  }
}

declare module "@mui/material/styles" {
  interface Palette {
    citation: Palette["primary"];
    primaryBackground: Palette["primary"];
    citationBackground: Palette["primary"];
    administratorHeaderBackground: Palette["primary"];
    drawerBackground: Palette["primary"];
    boxShadow: Palette["primary"];
    onHover: Palette["primary"];
    tableBackground: Palette["primary"];
  }
  interface PaletteOptions {
    citation?: PaletteOptions["primary"];
    primaryBackground?: PaletteOptions["primary"];
    citationBackground?: PaletteOptions["primary"];
    administratorHeaderBackground?: PaletteOptions["primary"];
    drawerBackground?: PaletteOptions["primary"];
    boxShadow?: PaletteOptions["primary"];
    onHover?: PaletteOptions["primary"];
    tableBackground?: PaletteOptions["primary"];
  }
}

export const theme = createTheme({
  palette: {
    primary: {
      main: blue[700],
    },
    secondary: {
      main: grey[700],
    },
    error: {
      main: red[700],
    },
    warning: {
      main: "#FFB74D",
    },
    success: {
      main: "#2E7D32",
    },
    citation: {
      main: "#368B7E",
    },
    text: {
      primary: "#212121",
    },
    primaryBackground: {
      main: "#F3F6F9",
    },
    citationBackground: {
      main: "#D1DBFA",
    },
    administratorHeaderBackground: {
      main: "#FFF4E5",
    },
    drawerBackground: {
      main: "#BDBDBD",
    },
    boxShadow: {
      main: "rgba(0, 0, 0, 0.1)",
    },
    onHover: {
      main: grey[100],
    },
    tableBackground: {
      main: grey[50],
    },
  },
  typography: {
    fontFamily: ["Noto Sans JP", "sans-serif"].join(","),
    h1: {
      fontSize: 24,
      fontWeight: 700,
    },
    h2: {
      fontSize: 22,
      fontWeight: 700,
    },
    h3: {
      fontSize: 20,
      fontWeight: 700,
    },
    h4: {
      fontSize: 18,
      fontWeight: 700,
    },
    h5: {
      fontSize: 16,
      fontWeight: 700,
    },
    h6: {
      fontSize: 14,
      fontWeight: 700,
    },
    subtitle1: {
      fontSize: 16,
      fontWeight: 500,
    },
    subtitle2: {
      fontSize: 14,
      fontWeight: 500,
    },
    body1: {
      fontSize: 16,
      fontWeight: 500,
    },
    body2: {
      fontSize: 14,
      fontWeight: 500,
    },
    button: {
      textTransform: "none",
      fontWeight: 700,
      fontSize: 14,
    },
  },
});

export const USER_TOKEN_CONSUMPTION_COLOR = theme.palette.primary.main;
export const API_KEY_COLOR = "#02B2AF";
export const PDF_PARSER_TOKEN_CONSUMPTION_COLOR = "#60009B";
export const DEFAULT_ASSISTANT_ICON_COLOR = "#AA68FF";
export const USER_AVATAR_ICON_COLOR = "#212121";
export const MODEL_COLORS: Record<string, string> = {
  gpt: "#404040",
  o1: "#404040",
  claude: "#CC6600",
  gemini: "#0080FF",
  default: "#696969",
};
