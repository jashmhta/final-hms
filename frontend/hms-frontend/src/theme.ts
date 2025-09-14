import { createTheme } from "@mui/material/styles";

export type MonoMode = "light" | "dark";

export function getMonoTheme(mode: MonoMode) {
  const isDark = mode === "dark";
  return createTheme({
    palette: {
      mode,
      primary: { main: isDark ? "#ffffff" : "#000000" },
      secondary: { main: isDark ? "#d0d0d0" : "#6e6e6e" },
      background: {
        default: isDark ? "#000000" : "#ffffff",
        paper: isDark ? "#000000" : "#ffffff",
      },
      text: {
        primary: isDark ? "#ffffff" : "#000000",
        secondary: isDark ? "#d0d0d0" : "#444444",
      },
      divider: isDark ? "#222222" : "#111111",
    },
    shape: { borderRadius: 8 },
    typography: {
      fontFamily: [
        "system-ui",
        "Inter",
        "Segoe UI",
        "Roboto",
        "Helvetica",
        "Arial",
        "sans-serif",
      ].join(","),
    },
    components: {
      MuiCssBaseline: {
        styleOverrides: {
          body: {
            backgroundColor: isDark ? "#000" : "#fff",
            color: isDark ? "#fff" : "#000",
          },
        },
      },
      MuiAppBar: {
        styleOverrides: {
          root: {
            backgroundColor: "#000000",
            color: "#ffffff",
            boxShadow: "0 1px 0 #e5e5e5",
          },
        },
      },
      MuiPaper: {
        styleOverrides: {
          root: {
            border: `1px solid ${isDark ? "#222" : "#111"}`,
            boxShadow: "none",
          },
        },
      },
      MuiButton: {
        defaultProps: {
          disableElevation: true,
          disableRipple: true,
        },
        styleOverrides: {
          root: {
            borderRadius: 8,
            textTransform: "none",
          },
          containedPrimary: {
            backgroundColor: isDark ? "#fff" : "#000",
            color: isDark ? "#000" : "#fff",
            "&:hover": { backgroundColor: isDark ? "#eaeaea" : "#111" },
          },
          outlined: {
            borderColor: isDark ? "#fff" : "#000",
            color: isDark ? "#fff" : "#000",
            "&:hover": {
              borderColor: isDark ? "#eaeaea" : "#111",
              backgroundColor: isDark ? "#111" : "#f5f5f5",
            },
          },
        },
      },
      MuiTextField: {
        defaultProps: {
          variant: "outlined",
        },
      },
      MuiListItem: {
        styleOverrides: {
          root: {
            borderBottom: "1px solid #eee",
          },
        },
      },
    },
  });
}

export default getMonoTheme;
