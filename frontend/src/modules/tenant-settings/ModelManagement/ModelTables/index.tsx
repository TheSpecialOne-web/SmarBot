import HelpOutlineIcon from "@mui/icons-material/HelpOutline";
import { Rating, Stack, Typography } from "@mui/material";
import { ReactNode } from "react";

import { IconButtonWithTooltip } from "@/components/buttons/IconButtonWithTooltip";
import { CustomTableSkeleton } from "@/components/loadings/TableSkeletonLoading";
import { Spacer } from "@/components/spacers/Spacer";
import { CustomTable, CustomTableColumn, Order } from "@/components/tables/CustomTable";
import { LEGACY_MODEL_FAMILIES, ModelFamilyDetail, modelFamilyDetails } from "@/const/modelFamily";
import { getComparator } from "@/libs/sort";

const sortModelFamilies = (
  modelFamilies: ModelFamilyDetail[],
  order: Order,
  orderBy: keyof ModelFamilyDetail,
) => {
  const comparator = getComparator<ModelFamilyDetail>(order, orderBy);
  return [...modelFamilies].sort(comparator);
};

const tableColumns: CustomTableColumn<ModelFamilyDetail>[] = [
  {
    key: "name",
    label: "モデル",
    align: "left",
    minWidth: 10,
    maxWidth: 200,
    render: (mf: ModelFamilyDetail) => (
      <Stack direction="row" alignItems="center">
        <Typography variant="subtitle2" noWrap>
          {mf.name}
        </Typography>
        {mf.tooltip && (
          <IconButtonWithTooltip
            tooltipTitle={mf.tooltip}
            color="primary"
            icon={<HelpOutlineIcon sx={{ fontSize: 18 }} />}
            iconButtonSx={{ p: 0.5 }}
          />
        )}
      </Stack>
    ),
  },
  {
    key: "accuracy",
    label: "精度",
    align: "left",
    minWidth: 10,
    render: (mf: ModelFamilyDetail) =>
      mf.accuracy === null ? "-" : <Rating precision={0.5} max={3} value={mf.accuracy} readOnly />,
    sortFunction: sortModelFamilies,
  },
  {
    key: "speed",
    label: "速さ",
    align: "left",
    minWidth: 10,
    render: (mf: ModelFamilyDetail) =>
      mf.speed === null ? "-" : <Rating precision={0.5} max={3} value={mf.speed} readOnly />,
    sortFunction: sortModelFamilies,
  },
  {
    key: "tokenConsumption",
    label: (
      <>
        <Typography
          variant="h6"
          sx={{
            width: "fit-content",
            textWrap: "nowrap",
          }}
        >
          消費トークン
        </Typography>
        <Spacer px={4} horizontal />
        <IconButtonWithTooltip
          tooltipTitle="消費トークンを計算する際に使用する係数です。値が大きいほどトークンの消費量が多くなります。"
          color="primary"
          icon={<HelpOutlineIcon sx={{ fontSize: 20 }} />}
          iconButtonSx={{ p: 0.5 }}
        />
      </>
    ),
    align: "right",
    cellSx: { pr: 9 },
    minWidth: 10,
    sortFunction: sortModelFamilies,
  },
  {
    key: "estimatedInputLength",
    label: (
      <>
        <Typography
          variant="h6"
          sx={{
            width: "fit-content",
            textWrap: "nowrap",
          }}
        >
          最大入力文字数
        </Typography>
        <Spacer px={4} horizontal />
        <IconButtonWithTooltip
          tooltipTitle="カスタム指示や取得したチャンクの文字数も含んだ概算値となります。"
          color="primary"
          icon={<HelpOutlineIcon sx={{ fontSize: 20 }} />}
          iconButtonSx={{ p: 0.5 }}
        />
      </>
    ),
    align: "right",
    cellSx: { pr: 9 },
    render: (mf: ModelFamilyDetail) =>
      mf.estimatedInputLength === null ? "-" : mf.estimatedInputLength.toLocaleString(),
    sortFunction: sortModelFamilies,
  },
  {
    key: "estimatedOutputLength",
    label: (
      <>
        <Typography
          variant="h6"
          sx={{
            width: "fit-content",
            textWrap: "nowrap",
          }}
        >
          最大出力文字数
        </Typography>
        <Spacer px={4} horizontal />
        <IconButtonWithTooltip
          tooltipTitle="概算となります。"
          color="primary"
          icon={<HelpOutlineIcon sx={{ fontSize: 20 }} />}
          iconButtonSx={{ p: 0.5 }}
        />
      </>
    ),
    align: "right",
    cellSx: { pr: 9 },
    render: (mf: ModelFamilyDetail) =>
      mf.estimatedOutputLength === null ? "-" : mf.estimatedOutputLength.toLocaleString(),
    sortFunction: sortModelFamilies,
  },
  {
    key: "overview",
    label: "概要",
    align: "left",
    minWidth: 10,
  },
];

type Props = {
  isLoading: boolean;
  modelFamiliesToDisplay?: ModelFamilyDetail[];
  renderActionColumn?: (modelFamily: ModelFamilyDetail) => ReactNode;
  showOverview?: boolean;
};

export const ModelTables = ({
  isLoading,
  modelFamiliesToDisplay,
  renderActionColumn,
  showOverview = true,
}: Props) => {
  if (isLoading) return <CustomTableSkeleton />;
  const tableData = (modelFamiliesToDisplay ? modelFamiliesToDisplay : modelFamilyDetails).filter(
    mf => !(LEGACY_MODEL_FAMILIES as string[]).includes(mf.id),
  );

  return (
    <CustomTable<ModelFamilyDetail>
      tableColumns={tableColumns.filter(column => column.key !== "overview" || showOverview)}
      tableData={tableData}
      renderActionColumn={renderActionColumn}
      hideControlHeader
    />
  );
};
