import DeleteOutlineIcon from "@mui/icons-material/DeleteOutline";
import { IconButton, Link } from "@mui/material";
import dayjs from "dayjs";

import { CustomTable, CustomTableColumn, Order } from "@/components/tables/CustomTable";
import { filterTest } from "@/libs/searchFilter";
import { getComparator } from "@/libs/sort";
import { Guideline } from "@/orval/models/backend-api";

const filterGuidelines = (guidelines: Guideline[], query: string) => {
  return guidelines.filter(guideline => {
    return filterTest(query, [guideline.filename]);
  });
};

const sortGuidelines = (guidelines: Guideline[], order: Order, orderBy: keyof Guideline) => {
  const comparator = getComparator<Guideline>(order, orderBy);
  return [...guidelines].sort(comparator);
};

type Props = {
  guidelines: Guideline[];
  onClickGuideline: (guideline: Guideline) => void;
  onClickDeleteIcon: (guideline: Guideline) => void;
};

export const TenantGuidelinesTable = ({
  guidelines,
  onClickGuideline,
  onClickDeleteIcon,
}: Props) => {
  const tableColumns: CustomTableColumn<Guideline>[] = [
    {
      key: "filename",
      label: "名前",
      align: "left",
      sortFunction: sortGuidelines,
      render: guideline => {
        return (
          <Link onClick={() => onClickGuideline(guideline)} sx={{ cursor: "pointer" }}>
            {guideline.filename}
          </Link>
        );
      },
    },
    {
      key: "created_at",
      label: "作成日",
      align: "left",
      sortFunction: sortGuidelines,
      render: guideline => dayjs(guideline.created_at).format("YYYY年M月D日"),
    },
  ];
  const renderActionColumn = (guideline: Guideline) => {
    return (
      <IconButton onClick={() => onClickDeleteIcon(guideline)}>
        <DeleteOutlineIcon color="error" />
      </IconButton>
    );
  };

  return (
    <CustomTable<Guideline>
      tableColumns={tableColumns}
      tableData={guidelines}
      searchFilter={filterGuidelines}
      renderActionColumn={renderActionColumn}
    />
  );
};
