from app.ingestion import get_collection

# This maintenance script clears all vector documents so startup indexing can rebuild them.
c = get_collection()
existing = c.get()

if existing["ids"]:
    c.delete(ids=existing["ids"])
    print(f"Deleted {len(existing['ids'])} old chunks")
else:
    print("Nothing to delete")
    