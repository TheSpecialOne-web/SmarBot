import { Accordion, AccordionDetails, AccordionSummary, styled } from "@mui/material";

export const StyledAccordion = styled(Accordion)(({ theme }) => ({
  border: `1px solid ${theme.palette.divider}`,
  borderRadius: theme.shape.borderRadius,
  boxShadow: "none", // デフォルトの影を削除
  "&:not(:last-child)": {
    marginBottom: theme.spacing(2), // Accordion 間にスペースを追加
  },
  "&:before": {
    display: "none",
  },
  "&.Mui-expanded": {
    margin: `${theme.spacing(2)} 0`, // 展開時のマージンを調整
  },
  transition: "margin 150ms cubic-bezier(0.4, 0, 0.2, 1) 0ms",
}));

export const StyledAccordionSummary = styled(AccordionSummary)(({ theme }) => ({
  borderBottom: `1px solid ${theme.palette.divider}`,
  "&.Mui-expanded": {
    minHeight: 48,
  },
  "& .MuiAccordionSummary-content.Mui-expanded": {
    margin: "12px 0",
  },
}));

export const StyledAccordionDetails = styled(AccordionDetails)(({ theme }) => ({
  padding: theme.spacing(2),
  borderTop: "none",
}));
