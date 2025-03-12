export const columns = [
  {
    accessorKey: "name",
    header: "模型名称",
  },
  {
    accessorKey: "base_url",
    header: "Base URL",
  },
  {
    accessorKey: "model_name",
    header: "模型名称参数",
  },
  {
    id: "actions",
    cell: ({ row }) => {
      const model = row.original
      return {
        _custom: {
          type: "actions",
          model
        }
      }
    },
  },
]