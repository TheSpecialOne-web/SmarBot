import NavigateNextIcon from "@mui/icons-material/NavigateNext";
import { Breadcrumbs as MuiBreadcrumbs, Link, Typography } from "@mui/material";

export type BreadcrumbsItem = {
  label: string;
  href?: string;
};

type Props = {
  items: BreadcrumbsItem[];
};

export const Breadcrumbs = ({ items }: Props) => {
  return (
    <MuiBreadcrumbs separator={<NavigateNextIcon fontSize="small" />}>
      {items.map(({ label, href }, index) =>
        href ? (
          <Link key={index} href={href}>
            {label}
          </Link>
        ) : (
          <Typography key={index}>{label}</Typography>
        ),
      )}
    </MuiBreadcrumbs>
  );
};
