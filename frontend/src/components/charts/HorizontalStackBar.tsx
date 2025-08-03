import { Box, Card, Divider, Stack, Typography } from "@mui/material";
import { grey } from "@mui/material/colors";
import { useState } from "react";

import { sumBy } from "@/libs/math";

type UsageData = {
  label: string;
  percent: number;
  color: string;
};

type Props = {
  data: UsageData[];
  showTotal?: boolean;
};

export const HorizontalStackBar = ({ data, showTotal = false }: Props) => {
  const [hoveredDataIndex, setHoveredDataIndex] = useState<number | null>(null);
  const [tooltipPosition, setTooltipPosition] = useState<{ left: number; top: number } | null>(
    null,
  );

  const totalPercent = sumBy<UsageData>(data, item => item.percent);

  const dataToShow =
    totalPercent >= 100
      ? data.filter(item => item.percent > 0)
      : [
          ...data.filter(item => item.percent > 0),
          {
            label: "残り",
            percent: 100 - totalPercent,
            color: grey[300],
          },
        ];

  return (
    <Stack
      direction="row"
      alignItems="center"
      width="100%"
      height="100%"
      justifyContent="space-between"
      gap={1}
    >
      <Stack direction="row" alignItems="center" width="100%" height="100%">
        {dataToShow.map((item, index) => (
          <Stack
            key={index}
            width={`${item.percent}%`}
            height={24}
            sx={{
              ":hover": { backgroundColor: grey[200] },
            }}
            justifyContent="center"
            onMouseEnter={() => setHoveredDataIndex(index)}
            onMouseMove={event =>
              setTooltipPosition({ left: event.clientX + 20, top: event.clientY + 2 })
            }
            onMouseLeave={() => {
              setHoveredDataIndex(null);
              setTooltipPosition(null);
            }}
          >
            <Box
              sx={{
                height: 4,
                backgroundColor: item.color,
                borderRadius:
                  dataToShow.length === 1
                    ? "4px"
                    : index === 0
                    ? "4px 0 0 4px"
                    : index === dataToShow.length - 1
                    ? "0 4px 4px 0"
                    : "",
              }}
            />
          </Stack>
        ))}
      </Stack>
      {showTotal && (
        <Typography variant="body2" color={totalPercent >= 100 ? "error" : grey[800]}>
          {`${Math.round(10 * totalPercent) / 10}%`}
        </Typography>
      )}
      {hoveredDataIndex !== null && (
        <Card
          elevation={1}
          sx={{
            position: "absolute",
            left: tooltipPosition?.left,
            top: tooltipPosition?.top,
            minWidth: "132px",
            zIndex: 9999,
          }}
        >
          <Stack direction={"column"} height={"100%"} width={"100%"} justifyContent="center">
            <Box paddingX={2} paddingY={1}>
              <Typography variant="subtitle2" color={grey[700]}>
                {dataToShow[hoveredDataIndex].label}
              </Typography>
            </Box>
            <Divider />
            <Stack
              direction={"row"}
              alignItems={"center"}
              justifyContent="space-between"
              paddingX={2}
              paddingY={1}
            >
              <Stack
                width={12}
                height={12}
                borderRadius={4}
                bgcolor="white"
                sx={{
                  boxShadow: 1,
                  alignItems: "center",
                  justifyContent: "center",
                }}
              >
                <Box
                  width={8}
                  height={8}
                  borderRadius={4}
                  bgcolor={dataToShow[hoveredDataIndex].color}
                />
              </Stack>
              <Typography>{`${
                Math.round(10 * dataToShow[hoveredDataIndex].percent) / 10
              }%`}</Typography>
            </Stack>
          </Stack>
        </Card>
      )}
    </Stack>
  );
};
