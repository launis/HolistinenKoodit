import ast

def verify_app_syntax():
    print("Verifying app.py syntax...")
    try:
        with open("src/app.py", "r", encoding="utf-8") as f:
            content = f.read()
        ast.parse(content)
        print("SUCCESS: app.py syntax is valid.")
        
        if 'st.tabs(["Orkestrointi", "Yksittäiset Agentit"])' in content:
            print("SUCCESS: Tabs swapped correctly.")
        else:
            print("FAILURE: Tabs not swapped.")
            
        if 'with st.expander(f"✅ {step[\'name\']} (Klikkaa nähdäksesi yksityiskohdat)"):' in content:
             print("SUCCESS: Expanders implemented.")
        else:
             print("FAILURE: Expanders missing.")
             
    except SyntaxError as e:
        print(f"FAILURE: Syntax error in app.py: {e}")
    except Exception as e:
        print(f"FAILURE: {e}")

if __name__ == "__main__":
    verify_app_syntax()
