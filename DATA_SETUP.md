# Data Setup for Custom Search App

## Required Excel Files

Place these files in the `data/` folder:

1. **category_pdp_plp.xlsx** - Category PDP/PLP data
2. **attributes.xlsx** - Attributes data  
3. **concat_rule.xlsx** - Concat rule data
4. **category_tree.xlsx** - Category tree data
5. **rejection_reasons.xlsx** - Rejection reasons data
6. **ptypes_dump.xlsx** - Product types data

## File Structure
```
data/
├── category_pdp_plp.xlsx
├── attributes.xlsx
├── concat_rule.xlsx
├── category_tree.xlsx
├── rejection_reasons.xlsx
└── ptypes_dump.xlsx
```

## Deployment Steps

1. **Add Excel files** to the `data/` folder
2. **Commit and push** to GitHub
3. **Redeploy** on Vercel
4. **Test** the endpoints

## Column Requirements

### category_pdp_plp.xlsx
- L0_category, L1_category, L1_category_id, L2_category, L2_category_id
- PDP1-PDP11, PLP1-PLP4

### attributes.xlsx  
- AttributeID, AttributeName, Source, "2"

### concat_rule.xlsx
- Category Name, L1, L2, Concat Rule

### category_tree.xlsx
- l0_category_id, l0_category, l1_category_id, l1_category, l2_category_id, l2_category

### rejection_reasons.xlsx
- Reason, Justification

### ptypes_dump.xlsx
- ptype_id, ptype_name

## Testing

After deployment, test each endpoint:
- `/pdp-plp` - Category PDP/PLP search
- `/attributes` - Attributes search  
- `/concat-rule` - Concat rule search
- `/category-tree` - Category tree search
- `/rejections` - Rejections search
- `/ptypes-dump` - Product types search 