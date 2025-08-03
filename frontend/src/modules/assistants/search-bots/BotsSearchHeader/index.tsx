import { Box, Tab, Tabs } from "@mui/material";

import { SearchField } from "@/components/inputs/SearchField";
import { Spacer } from "@/components/spacers/Spacer";
import { BotsSearchTab } from "@/types/botsSearchTab";

type Props = {
  selectedTab: string;
  searchQuery: string;
  handleSearchChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
  handleChangeTab: (_: React.ChangeEvent<object>, newTabKey: BotsSearchTab) => void;
};

export const BotsSearchHeader = ({
  selectedTab,
  searchQuery,
  handleSearchChange,
  handleChangeTab,
}: Props) => {
  return (
    <Box
      sx={{
        position: "sticky",
        top: 0,
        zIndex: 1,
        width: "100%",
        pt: 3,
        pb: 0,
      }}
    >
      <SearchField
        value={searchQuery}
        onChange={handleSearchChange}
        fullWidth
        size="medium"
        text="アシスタントを探す"
        borderRadius={4}
      />
      <Spacer px={2} />
      {!searchQuery && (
        <Tabs value={selectedTab} onChange={handleChangeTab}>
          <Tab
            label="お気に入り"
            value={BotsSearchTab.Liked}
            sx={{
              fontWeight: "bold",
              minWidth: 60,
              p: 1,
              pb: 0,
            }}
          />
          <Tab
            label="基盤モデル"
            value={BotsSearchTab.BasicAi}
            sx={{
              fontWeight: "bold",
              minWidth: 60,
              p: 1,
              pb: 0,
            }}
          />
          <Tab
            label="すべて"
            value={BotsSearchTab.All}
            sx={{
              fontWeight: "bold",
              minWidth: 60,
              p: 1,
              pb: 0,
            }}
          />
        </Tabs>
      )}
    </Box>
  );
};
