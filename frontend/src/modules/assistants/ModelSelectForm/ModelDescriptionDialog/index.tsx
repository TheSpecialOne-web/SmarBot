import HelpOutlineIcon from "@mui/icons-material/HelpOutline";
import { Button, DialogContent, Divider, Rating, Stack, Typography } from "@mui/material";

import { IconButtonWithTooltip } from "@/components/buttons/IconButtonWithTooltip";
import { CustomDialog } from "@/components/dialogs/CustomDialog";
import { Spacer } from "@/components/spacers/Spacer";
import { CustomTable, CustomTableColumn, Order } from "@/components/tables/CustomTable";
import { ModelFamilyDetail, modelFamilyDetails } from "@/const/modelFamily";
import { isModelFamily } from "@/libs/model";
import { getComparator } from "@/libs/sort";
import { ModelFamily } from "@/orval/models/backend-api";

const sortModelFamilyDetails = (
  details: ModelFamilyDetail[],
  order: Order,
  orderBy: keyof ModelFamilyDetail,
) => {
  const comparator = getComparator<ModelFamilyDetail>(order, orderBy);
  return [...details].sort(comparator);
};

type Props = {
  open: boolean;
  onClose: () => void;
  modelFamilies: ModelFamily[];
  onSelect: (modelFamily: ModelFamily) => void;
};

export const ModelDescriptionDialog = ({ open, onClose, modelFamilies, onSelect }: Props) => {
  const availableModelFamilyDetails = modelFamilyDetails.filter(modelFamilyDetail =>
    modelFamilies.includes(modelFamilyDetail.id as ModelFamily),
  );
  const maxStarCount = availableModelFamilyDetails.reduce((acc, detail) => {
    if (!detail.accuracy || !detail.speed) {
      return acc;
    }
    return Math.max(acc, detail.accuracy, detail.speed);
  }, 0);

  const tableColumns: CustomTableColumn<ModelFamilyDetail>[] = [
    {
      key: "name",
      label: <Typography variant="h6">モデル名</Typography>,
      align: "left",
      sortFunction: sortModelFamilyDetails,
      render: detail => (
        <Stack direction="row" alignItems="center">
          <Typography variant="subtitle2">{detail.name}</Typography>
          {detail.tooltip && (
            <IconButtonWithTooltip
              tooltipTitle={detail.tooltip}
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
      label: <Typography variant="h6">精度</Typography>,
      align: "center",
      minWidth: 100,
      render: detail => (
        <Rating precision={0.5} value={detail.accuracy} max={maxStarCount} readOnly />
      ),
      sortFunction: sortModelFamilyDetails,
    },
    {
      key: "speed",
      label: <Typography variant="h6">速さ</Typography>,
      align: "center",
      minWidth: 100,
      render: detail => <Rating precision={0.5} value={detail.speed} max={maxStarCount} readOnly />,
      sortFunction: sortModelFamilyDetails,
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
            tooltipTitle="数字が大きいほど割り当てられたトークンの消費が多いことを示します。"
            color="primary"
            icon={<HelpOutlineIcon sx={{ fontSize: 20 }} />}
            iconButtonSx={{ p: 0.5 }}
          />
        </>
      ),
      align: "right",
      cellSx: { pr: 9 },
      minWidth: 100,
      sortFunction: sortModelFamilyDetails,
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
      minWidth: 100,
      cellSx: { pr: 9 },
      render: (mf: ModelFamilyDetail) => {
        if (!mf.estimatedInputLength) return;
        return mf.estimatedInputLength.toLocaleString();
      },
      sortFunction: sortModelFamilyDetails,
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
      minWidth: 100,
      cellSx: { pr: 9 },
      render: (mf: ModelFamilyDetail) => {
        if (!mf.estimatedOutputLength) return;
        return mf.estimatedOutputLength.toLocaleString();
      },
      sortFunction: sortModelFamilyDetails,
    },
    {
      key: "id",
      label: "",
      align: "center",
      minWidth: 100,
      render: modelFamily =>
        isModelFamily(modelFamily.id) && (
          <Button
            variant="outlined"
            onClick={() => onSelect(modelFamily.id as ModelFamily)}
            sx={{ p: 0.1 }}
          >
            選択
          </Button>
        ),
    },
  ];

  return (
    <CustomDialog title="モデル一覧" open={open} onClose={onClose} maxWidth="lg">
      <Divider />
      <DialogContent>
        <CustomTable
          tableColumns={tableColumns}
          tableData={availableModelFamilyDetails}
          hideControlHeader={true}
        />
      </DialogContent>
    </CustomDialog>
  );
};
