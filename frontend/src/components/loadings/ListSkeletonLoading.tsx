import { Skeleton } from "@mui/material";

type Props = {
  rowsCount?: number;
  rowHeight?: number;
};

export const ListSkeletonLoading = ({ rowsCount = 10, rowHeight = 40 }: Props) => {
  return (
    <>
      {Array.from({ length: rowsCount }).map((_, index) => (
        <Skeleton key={index} width="100%" height={rowHeight} />
      ))}
    </>
  );
};
