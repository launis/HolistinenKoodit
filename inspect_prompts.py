from src.prompt_splitter import PromptSplitter

def inspect():
    splitter = PromptSplitter()
    if not splitter.split_document():
        print("Failed to split document")
        return

    common = splitter.modules.get('COMMON_RULES', '')
    phase1 = splitter.modules.get('VAIHE 1', '')

    print(f"Common Rules length: {len(common)}")
    print(f"Phase 1 length: {len(phase1)}")

    search_term = "ÄSKE"
    
    if search_term in common:
        print(f"FOUND '{search_term}' in COMMON_RULES")
        # Print context
        idx = common.find(search_term)
        print(f"Context: ...{common[idx:idx+200]}...")
    else:
        print(f"NOT FOUND '{search_term}' in COMMON_RULES")

    if search_term in phase1:
        print(f"FOUND '{search_term}' in VAIHE 1")
        idx = phase1.find(search_term)
        print(f"Context: ...{phase1[idx:idx+200]}...")
    else:
        print(f"NOT FOUND '{search_term}' in VAIHE 1")

if __name__ == "__main__":
    inspect()
