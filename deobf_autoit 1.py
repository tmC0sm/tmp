import math
import os
import re
import sys

def delete_for_0_to_0_loops(script):
    print("Look for 'For 0 To 0' loops :")
    new_script = []
    nb_loops_deleted = 0
    i = 0
    while i<len(script):
        if script[i].strip(" \t\n")[0:4] == "For ":
            m = re.search(r"[ \t]*For .* = 0 To 0[ \t\n]*", script[i].strip(" \t\n"))
            if m is not None:
                print(f"    'For 0 To 0' loop found at line {i}...")
                while script[i].strip(" \t\n") != "Next":
                    i += 1
                print(f"        ...and deleted until line {i}")
                nb_loops_deleted += 1
        else:
            new_script.append(script[i])
        i += 1
    print(f"    {nb_loops_deleted} loops deleted")
    return nb_loops_deleted, new_script
            
def replace_constants_functions(script):
    new_script = []
    nb_constant_functions = 0
    i = 0
    while 1:
        constant_function_found = False
        while i<len(script):
            if script[i].strip(" \t")[0:5] == "Func ":
                start_func = i
                while script[i].strip(" \t").find("EndFunc") != 0:
                    i += 1
                # There is a function to processed
                m = re.search(r"Func ([A-Za-z_][0-9A-Za-z_]*)\((.*)\)", script[start_func])
                if m is None:
                    print(f"Error processing function at line {i} !")
                    sys.exit(1)
                print(f"Processing function {m.group(1)}...")
                arguments = m.group(2).split(",")
                abort = False
                for arg in arguments:
                    for j in range(start_func+1, i):
                        a = arg.strip(" \t")
                        if script[j].find(a) != -1:
                            print(f"    -> argument {a} used")
                            abort = True
                            break
                if abort == True:
                    # keep function body in source
                    for j in range(start_func,i+1):
                        new_script.append(script[j])
                else:
                    print(f"    Function {m.group(1)} has fake arguments !")
                    # Try to get constant value returned by function
                    # Create autoit script with function and write result to "res.txt"
                    with open("c:\\tmp\\test.au3", "rt") as f:
                        f.write("#include \"<FileConstants.au3>\"\n")
                        f.write(f"$res = {m.group(1)}()\n")
                        f.write("$h = FileOpen(\"res.txt\", $FO_CREATE)\n")
                        f.write("FileWrite($h, $res)\n")
                        f.write("FileClose($h)\n")
                        f.write("""Func Vderisxfcsds(Const ByRef $aArray, $sDelim_Col = "|", $iStart_Row = -1, $iEnd_Row = -1, $sDelim_Row = @CRLF, $iStart_Col = -1, $iEnd_Col = -1)
	If $sDelim_Col = Default Then $sDelim_Col = "|"
	If $sDelim_Row = Default Then $sDelim_Row = @CRLF
	If $iStart_Row = Default Then $iStart_Row = -1
	If $iEnd_Row = Default Then $iEnd_Row = -1
	If $iStart_Col = Default Then $iStart_Col = -1
	If $iEnd_Col = Default Then $iEnd_Col = -1
	If Not IsArray($aArray) Then Return SetError(1, 0, -1)
	Local $iDim_1 = UBound($aArray, 1) - 1
	If $iStart_Row = -1 Then $iStart_Row = 0
	If $iEnd_Row = -1 Then $iEnd_Row = $iDim_1
	If $iStart_Row < -1 Or $iEnd_Row < -1 Then Return SetError(3, 0, -1)
	If $iStart_Row > $iDim_1 Or $iEnd_Row > $iDim_1 Then Return SetError(3, 0, "")
	If $iStart_Row > $iEnd_Row Then Return SetError(4, 0, -1)
	Local $sRet = ""
	Switch UBound($aArray, 0)
		Case 1
			For $i = $iStart_Row To $iEnd_Row
				$sRet &= $aArray[$i] & $sDelim_Col
			Next
			Return StringTrimRight($sRet, StringLen($sDelim_Col))
		Case 2
			Local $iDim_2 = UBound($aArray, 2) - 1
			If $iStart_Col = -1 Then $iStart_Col = 0
			If $iEnd_Col = -1 Then $iEnd_Col = $iDim_2
			If $iStart_Col < -1 Or $iEnd_Col < -1 Then Return SetError(5, 0, -1)
			If $iStart_Col > $iDim_2 Or $iEnd_Col > $iDim_2 Then Return SetError(5, 0, -1)
			If $iStart_Col > $iEnd_Col Then Return SetError(6, 0, -1)
			For $i = $iStart_Row To $iEnd_Row
				For $j = $iStart_Col To $iEnd_Col
					$sRet &= $aArray[$i][$j] & $sDelim_Col
				Next
				$sRet = StringTrimRight($sRet, StringLen($sDelim_Col)) & $sDelim_Row
			Next
			Return StringTrimRight($sRet, StringLen($sDelim_Row))
		Case Else
			Return SetError(2, 0, -1)
	EndSwitch
	Return 1
EndFunc""")
                        f.write(f"Func {m.group(1)}()")
                        for j in range(start_func+1, i):
                            f.write(script[j])
                    # Launch auotit interpreter
                    os.system("C:\\FlareTools\\AutoIt3.exe C:\\tmp\\script.au3")
                    # Read result from result file
                    new_script.append("\n# Function with unused arguments\n")
                    with open("res.txt", "rt") as f:
                        res = f.read()
                    # End this pass
                    while i<len(script):
                        new_script.append(script[i])
                    # replace function calls with result
                    new_script2 = []
                    for line in new_script:
                        m1 = re.search(f"({m.group(1)}\(.*\))", line)
                        if m1 is not None:
                            line.replace(m1.group(1), res)
                        new_script2.append(line)
                    script = new_script2        
                    constant_function_found = True
                    nb_constants_functions += 1 
                    break
            else:
                new_script.append(script[i])
            i += 1
        if constant_function_found == False:
            break

    print(f"    {nb_constants_functions} constants functions detected.")
    return nb_constants_fuctions, new_script
            
def group_multi_lines(script):
    print("Look for multi-lines...")
    new_script = []
    nb_grouped = 0
    new_line = ""
    for line in script:
        if len(line.strip(" \t\n")) == 0:
            new_script.append(line)
        elif line.strip(" \t\n")[-2:] != ' _':
            if new_line != "":
                new_line += line.strip(" \t")
                new_script.append(new_line)
                new_line = ""
                nb_grouped += 1
            else:
                new_script.append(line)
        else:
            if new_line != "":
                line = line.strip(" _\t\n")
            else:
                line = line.strip("_\n")
            print(f"    multi-lines : '{line}'")
            new_line += line+" "
    print(f"    {nb_grouped} re-grouped lines.")
    return nb_grouped, new_script
       
def replace_constants_arrays(script):
    print("Look for arrays of constants...")
    list_of_strings_to_replace = []
    nb_replaced = 0
    for line in script:
        m = re.search(r"Global (?:Const )?(\$[0-9A-Za-z_]+)\[[0-9]+\] = \[([0-9, ].*)\]", line)
        if m is not None:
            print(f"Global constants array found : '{m.group(1)}'")
            elements_values = []
            all_elements_types_ok = True
            elements = m.group(2).split(",")
            for e in elements:
                e = e.strip(" \t")
                m1 = re.search(r"^\".*\"$", e)
                if m1 is not None:
                    # print(f"{e} => string")
                    elements_values.append(e)
                    continue
                m1 = re.search(r"^[0-9]+$", e)
                if m1 is not None:
                    # print(f"{e} => int")
                    elements_values.append(e)
                    continue
                print(f"{e} => unknown element type")
                all_elements_types_ok = False
            if all_elements_types_ok:
                print(f"    {m.group(1)} found")
                # Add strings to replacement list
                i=0
                for e in elements_values:
                    list_of_strings_to_replace.append([f"{m.group(1)}[{i}]", e])
                    i += 1
    # now replace all strings in replacement list
    for s in list_of_strings_to_replace:
        # print(s)
        nb, script = replace_string_in_script(script, s[0], s[1])
        nb_replaced += nb
    print(f"    {nb_replaced} values replaced")
    return nb_replaced, script

def replace_two_dimensions_constants_arrays(script):
    print("Look for two dimensions arrays of constants...")
    list_of_strings_to_replace = []
    nb_replaced = 0
    for line in script:
        m = re.search(r"Global (?:Const )?(\$[0-9A-Za-z_]+)\[[0-9]+\]\[[0-9]+\] = \[\[([0-9, ]+)\], *\[([0-9, ]+)\]\]", line)
        if m is not None:
            print(f"    Global constants two dimensions array found : '{m.group(1)}'")
            elements_values_dimension_1 = []
            all_elements_types_ok = True
            elements = m.group(2).split(",")
            for e in elements:
                e = e.strip(" \t")
                m1 = re.search(r"^\".*\"$", e)
                if m1 is not None:
                    # print(f"{e} => string")
                    elements_values_dimension_1.append(e)
                    continue
                m1 = re.search(r"^[0-9]+$", e)
                if m1 is not None:
                    # print(f"{e} => int")
                    elements_values_dimension_1.append(e)
                    continue
                print(f"{e} => unknown element type")
                all_elements_types_ok = False
            elements_values_dimension_2 = []
            elements = m.group(3).split(",")
            for e in elements:
                e = e.strip(" \t")
                m1 = re.search(r"^\".*\"$", e)
                if m1 is not None:
                    # print(f"{e} => string")
                    elements_values_dimension_2.append(e)
                    continue
                m1 = re.search(r"^[0-9]+$", e)
                if m1 is not None:
                    # print(f"{e} => int")
                    elements_values_dimension_2.append(e)
                    continue
                print(f"{e} => unknown element type")
                all_elements_types_ok = False
            if all_elements_types_ok:
                # Add strings to replacement list
                for i in range(len(elements_values_dimension_1)):
                    list_of_strings_to_replace.append([f"{m.group(1)}[0][{i}]",
                                                       elements_values_dimension_1[i]])
                for i in range(len(elements_values_dimension_2)):
                    list_of_strings_to_replace.append([f"{m.group(1)}[1][{i}]",
                                                       elements_values_dimension_2[i]])
    # now replace all strings in replacement list
    for s in list_of_strings_to_replace:
        nb, script = replace_string_in_script(script, s[0], s[1])
        nb_replaced += nb
    print(f"    {nb_replaced} values replaced.")
    return nb_replaced, script

def replace_string_in_script(script, s_source, s_dest):
    nb_replaced = 0
    new_script = []
    for line in script:
        while line.find(s_source) != -1:
            line = line.replace(s_source, s_dest, 1)
            print(f"    Replacing '{s_source} by '{s_dest}'")
            nb_replaced += 1
        new_script.append(line)
    return nb_replaced, new_script

def replace_global_string_in_script(script, s_source, s_dest):
    new_script = []
    for line in script:
        if line.strip(" \t\n") != f"Global {s_source} = {s_dest}":
            new_script.append(line.replace(s_source, s_dest))
            print(f"    Replacing '{s_source}' by '{s_dest}'")
    return new_script

def replace_globals_functions_aliases(script):
    print("Look for functions aliases...")
    nb_replaced = 0
    globals_to_replace = []
    for line in script:
        m = re.search(r"[ \t]*Global (\$[a-zA-Z0-9_]+) = ([0-9A-Za-z_]+)[ \n]*", line)
        if m is not None:
            globals_to_replace.append({"source": m.group(1), "dest": m.group(2)})
            print(f"Probable function alias '{m.group(1)}' to '{m.group(2)}' found.")
    # Now replace strings where the global is used only to call function
    for g in globals_to_replace:
        abort = False
        for line in script:
            if re.search(r"[ \t]*Global (\$[a-zA-Z0-9_]+) = ([0-9A-Za-z_]+)[ \n]*", line) is None and \
               line.find(g["source"]) != -1 and line.find(g["source"]+"(") == -1 :
                print(f"    -> {g['source']} is not a function alias : {line}")
                abort = True
                break
        if abort == False:
            print(f"    -> Function alias '{g['source']}' replaced by '{g['dest']}'")
            script = replace_global_string_in_script(script, g["source"], g["dest"])
            nb_replaced += 1
    print(f"    {nb_replaced} functions aliases replaced.")
    return nb_replaced, script

def replace_globals_numerics(script):
    """
    Remplace toutes les variables globales numériques par leurs valeurs
    """
    print("Look for numerics globals...")
    nb_replaced = 0
    globals_to_replace = []
    for line in script:
        m = re.search(r"[ \t]*Global (\$[a-zA-Z0-9_]+) = ([0-9]+)[ \n]*", line)
        if m is not None:
            globals_to_replace.append({"source": m.group(1), "dest": m.group(2)})
    # Now replace 
    for g in globals_to_replace:
        print(f"    Replacing '{g['source']}' by '{g['dest']}'")
        script = replace_global_string_in_script(script,g["source"], g["dest"])
        nb_replaced += 1
    print(f"    {nb_replaced} numerics globals replaced.")
    return nb_replaced, script

def rol(n,rotations,width):
    return (2**width-1)&(n<<rotations|n>>(width-rotations))

def ror(n,rotations,width):
    return (2**width-1)&(n>>rotations|n<<(width-rotations))

def replace_simples_bitrotates(script):
    """
    Remplace tous les BitRotate() par leur valeur numérique
    """
    iNbReplaces = 0
    new_script = []
    for line in script:
        for m in re.searchiter(r"BitRotate\(([0-9]{1,12}), (\-{0,1}[0-9]{1,2}), \"D\"\)", line, re.S):
            if int(m.group(2)) < 0:
                res = ror(int(m.group(1)), -int(m.group(2)), 32)
            else:
                res = ror(int(m.group(1)), int(m.group(2)), 32)
            line = line.replace(f"BitRotate({m.group(1)}, {m.group(2)}, \"D\")", f"{res}")
            iNbReplaces += 1
            print(f"'BitRotate({m.group(1)}, {m.group(2)}, \"D\")' replaced by {res}")
        new_script.append(line)
    print(f"{iNbReplaces} BitRotates processed")
    return iNbReplaces, new_script

def replace_StringMid(script):
    """
    Replace StringMid(constant, constant, constant) by string value
    """
    print("Look for StringMid...")
    nb_replaced = 0
    new_script = []
    for line in script:
        for m in re.searchiter(r"StringMid\(\"(.*)\", ([0-9]+), ([0-9]+)\)", line, re.S):
            res = m.group(1)[int(m.group(2))-1:int(m.group(2))-1+int(m.group(3))]
            line = line.replace(f"StringMid(\"{m.group(1)}\", {m.group(2)}, {m.group(3)})", f"\"{res}\"")
            nb_replaced += 1
            print(f"    'StringMid(\"{m.group(1)}\", {m.group(2)}, {m.group(3)})' replaced by '\"{res}\"'")
        new_script.append(line)
    print(f"    {nb_replaced} 'StringMid' processed.")
    return nb_replaced, new_script

def replace_StringTrimLeft(script):
    """
    Replace StringTrimLeft(constant, constant, constant) by string value
    """
    print("Look for StringTrimLeft...")
    nb_replaced = 0
    new_script = []
    for line in script:
        for m in re.searchiter(r"StringTrimLeft\(\"(.*)\", ([0-9]+)\)", line, re.S):
            res = m.group(1)[int(m.group(2)):]
            line = line.replace(f"StringTrimLeft(\"{m.group(1)}\", {m.group(2)})", f"\"{res}\"")
            nb_replaced += 1
            print(f"    'StringTrimLeft(\"{m.group(1)}\", {m.group(2)})' replaced by '\"{res}\"'")
        new_script.append(line)
    print(f"    {nb_replaced} 'StringTrimLeft' processed.")
    return nb_replaced, new_script

def replace_StringTrimRight(script):
    """
    Replace StringTrimRight(constant, constant, constant) by string value
    """
    print("Look for StringTrimRight...")
    nb_replaced = 0
    new_script = []
    for line in script:
        for m in re.searchiter(r"StringTrimRight\(\"(.*)\", ([0-9]+)\)", line, re.S):
            res = m.group(1)[:-int(m.group(2))]
            line = line.replace(f"StringTrimRight(\"{m.group(1)}\", {m.group(2)})", f"\"{res}\"")
            nb_replaced += 1
            print(f"    'StringTrimRight(\"{m.group(1)}\", {m.group(2)})' replaced by '\"{res}\"'")
        new_script.append(line)
    print(f"    {nb_replaced} 'StringTrimRight' processed.")
    return nb_replaced, new_script

def replace_Asc(script):
    """
    Replace Asc(constant) by int value
    """
    nb_replaced = 0
    new_script = []
    for line in script:
        for m in re.searchiter(r"Asc\(\"(.)\"\)", line, re.S):
            res = ord(m.group(1))
            line = line.replace(f"Asc(\"{m.group(1)}\")", f"{res}")
            nb_replaced += 1
            print(f"    'Asc(\"{m.group(1)}\")' replaced by ' {res}'")
        new_script.append(line)
    print(f"    {nb_replaced} 'Asc' processed.")
    return nb_replaced, new_script

def replace_Chr(script):
    """
    Replace Chr(constant) by int value
    """
    nb_replaced = 0
    new_script = []
    for line in script:
        for m in re.searchiter(r"Chr\(([0-9]+)\)", line, re.S):
            res = chr(int(m.group(1)))
            line = line.replace(f"Chr({m.group(1)})", f"{res}")
            nb_replaced += 1
            print(f"    'Chr({m.group(1)})' replaced by ' {res}'")
        new_script.append(line)
    print(f"    {nb_replaced} 'Chr' processed.")
    return nb_replaced, new_script

def replace_minus_int(script):
    """
    Remplace tous les -(-i) par leur valeur numérique
    """
    iNbReplaces = 0
    new_script = []
    for line in script:
        for m in re.searchiter(r" \-\(\-([0-9]{1,12})\)", line, re.S):
            res = m.group(1)
            line = line.replace(f" -(-{m.group(1)})", f" {res}")
            iNbReplaces += 1
            print(f"' -(-{m.group(1)})' replaced by ' {res}'")
        new_script.append(line)
    print(f"{iNbReplaces} ' -(-' processed")
    return iNbReplaces, new_script


def replace_bitnot(script):
    """
    Remplace tous les BitNOT() par leur valeur numérique
    """
    iNbReplaces = 0
    new_script = []
    for line in script:
        for m in re.searchiter(r"BitNOT\((\-{0,1}[0-9]{1,12})\)", line, re.S):
            res = ~int(m.group(1))
            line = line.replace(f"BitNOT({m.group(1)})", f"{res}")
            iNbReplaces += 1
            print(f"'BitNOT({m.group(1)})' replaced by {res}")
        new_script.append(line)
    print(f"{iNbReplaces} BitNOT processed")
    return iNbReplaces, new_script

def replace_bitand(script):
    """
    Remplace tous les BitAND() par leur valeur numérique
    """
    iNbReplaces = 0
    new_script = []
    for line in script:
        for m in re.searchiter(r"BitAND\((\-{0,1}[0-9]{1,12}), (\-{0,1}[0-9]{1,12})\)", line, re.S):
            res = int(m.group(1)) & int(m.group(2))
            line = line.replace(f"BitAND({m.group(1)}, {m.group(2)})", f"{res}")
            iNbReplaces += 1
            print(f"'BitAND({m.group(1)}, {m.group(2)})' replaced by {res}")
        new_script.append(line)
    print(f"{iNbReplaces} BitAND processed")
    return iNbReplaces, new_script

def replace_bitor(script):
    """
    Remplace tous les BitOR() par leur valeur numérique
    """
    iNbReplaces = 0
    new_script = []
    for line in script:
        for m in re.searchiter(r"BitOR\((\-{0,1}[0-9]{1,12}), (\-{0,1}[0-9]{1,12})\)", line, re.S):
            res = int(m.group(1)) | int(m.group(2))
            line = line.replace(f"BitOR({m.group(1)}, {m.group(2)})", f"{res}")
            iNbReplaces += 1
            print(f"'BitOR({m.group(1)}, {m.group(2)})' replaced by {res}")
        new_script.append(line)
    print(f"{iNbReplaces} BitOR processed")
    return iNbReplaces, new_script

def replace_bitxor(script):
    """
    Remplace tous les BitXOR() par leur valeur numérique
    """
    iNbReplaces = 0
    new_script = []
    for line in script:
        for m in re.searchiter(r"BitXOR\((\-{0,1}[0-9]{1,12}), (\-{0,1}[0-9]{1,12})\)", line, re.S):
            res = int(m.group(1)) ^ int(m.group(2))
            line = line.replace(f"BitXOR({m.group(1)}, {m.group(2)})", f"{res}")
            iNbReplaces += 1
            print(f"'BitXOR({m.group(1)}, {m.group(2)})' replaced by {res}")
        new_script.append(line)
    print(f"{iNbReplaces} BitXOR processed")
    return iNbReplaces, new_script

def replace_numeric_addition(script):
    """
    Remplace toutes les aditions numériques par leur valeur numérique
    """
    iNbReplaces = 0
    new_script = []
    for line in script:
        for m in re.searchiter(r"(\-{0,1}[0-9]{1,12}) \+ (\-{0,1}[0-9]{1,12})", line, re.S):
            res = int(m.group(1)) + int(m.group(2))
            line = line.replace(f"{m.group(1)} + {m.group(2)}", f"{res}")
            iNbReplaces += 1
            print(f"'{m.group(1)} + {m.group(2)}' replaced by '{res}'")
        new_script.append(line)
    print(f"{iNbReplaces} numeric additions processed")
    return iNbReplaces, new_script

def replace_numeric_soustraction(script):
    """
    Remplace toutes les soustractions numériques par leur valeur numérique
    """
    iNbReplaces = 0
    new_script = []
    for line in script:
        for m in re.searchiter(r"(\-{0,1}[0-9]{1,12}) - (\-{0,1}[0-9]{1,12})", line, re.S):
            res = int(m.group(1)) - int(m.group(2))
            line = line.replace(f"{m.group(1)} - {m.group(2)}", f"{res}")
            iNbReplaces += 1
            print(f"'{m.group(1)} - {m.group(2)}' replaced by '{res}'")
        new_script.append(line)
    print(f"{iNbReplaces} numeric soustractions processed")
    return iNbReplaces, new_script

def replace_StringReverse(script):
    """
    Remplace toutes les commandes StringReverse de chaînes statiques
    """
    iNbReplaces = 0
    new_script = []
    for line in script:
        for m in re.searchiter(r'StringReverse\("(.*)"\)', line, re.S):
            res = m.group(1)[::-1]
            line = line.replace(f"StringReverse(\"{m.group(1)}\")", f"\"{res}\"")
            iNbReplaces += 1
            print(f"'StringReverse(\"{m.group(1)}\")' replaced by '\"{res}\"'")
        new_script.append(line)
    print(f"{iNbReplaces} StringReverse processed")
    return iNbReplaces, new_script

def replace_Sqrt(script):
    """
    Remplace toutes les commandes Sqrt de nombres statiques
    """
    iNbReplaces = 0
    new_script = []
    for line in script:
        for m in re.searchiter(r'Sqrt\(([0-9]+)\)', line, re.S):
            res = math.sqrt(int(m.group(1)))
            line = line.replace(f"Sqrt({m.group(1)})", f"{res}")
            iNbReplaces += 1
            print(f"'Sqrt({m.group(1)})' replaced by '{res}'")
        new_script.append(line)
    print(f"{iNbReplaces} Sqrt processed")
    return iNbReplaces, new_script

def replace_string_concatenation(script):
    """
    Replace constants strings concatenations
    """
    nb_replaced = 0
    new_script = []
    for line in script:
        for m in re.searchiter(r'\"(.*)\" & \"(.*)\"', line, re.S):
            res = m.group(1) + m.group(2)
            line = line.replace(f"\"{m.group(1)}\" & \"{m.group(2)}\"", f"\"{res}\"")
            nb_replaced += 1
            print(f"'\"{m.group(1)}\" & \"{m.group(2)}\"' replaced by '\"{res}\"'")
        new_script.append(line)
    print(f"{nb_replaced} & processed")
    return nb_replaced, new_script



def look_for_simple_do_switch(script):
    iNbDo = 0
    i=0
    while i<len(script):
        while i<len(script) and script[i].strip("\n\t ") != "Do":
            i += 1
        j=i
        if  j<len(script):
            print("'Do' found")
            m = re.match(r"Until.*", script[j].strip("\n\t "))
            while j<len(script) and m is None:
                j += 1
                m = re.match(r"Until.*", script[j].strip("\n\t "))
        if j<len(script):
            print(f"Do...Until : {i},{j}")
            iNbDo += 1
        i=j+1
    return iNbDo

def defeat_obfuscation_loops(obfuscated_script):

    obfuscation_loops = [m.span() for m in re.searchiter(r'\$\w+\s*=\s*\d+\n\$\w+\s*=\s*\d+\nDo\nSwitch\s*\$\w+.*?EndSwitch\nUntil\s*.*?\n', obfuscated_script, re.DOTALL)]

    first_loop = obfuscated_script[obfuscation_loops[0][0]:obfuscation_loops[0][1] + 1]
    case_number = re.search(r'\$\w+\s*=\s*(\d+)', first_loop).group(1)
    statements = re.search(f'Case\s+{case_number}(.*)ExitLoop', first_loop, re.DOTALL).group(1)
    deobfuscated_script = obfuscated_script[:obfuscation_loops[0][0]] + statements

    for loop_index in range(1, len(obfuscation_loops)):
        deobfuscated_script += obfuscated_script[obfuscation_loops[loop_index - 1][1]: obfuscation_loops[loop_index][0]]
        obfuscated_loop = obfuscated_script[obfuscation_loops[loop_index][0]: obfuscation_loops[loop_index][1] + 1]

        case_number = re.search(r'\$\w+\s*=\s*(\d+)', obfuscated_loop).group(1)
        statements = re.search(f'Case\s+{case_number}(.*)ExitLoop', obfuscated_loop, re.DOTALL).group(1)
        deobfuscated_script += statements

    last_loop = obfuscated_script[obfuscation_loops[-1][0]:obfuscation_loops[-1][1] + 1]
    case_number = re.search(r'\$\w+\s*=\s*(\d+)', last_loop).group(1)
    statements = re.search(f'Case\s+{case_number}(.*)ExitLoop', last_loop, re.DOTALL).group(1)
    deobfuscated_script += obfuscated_script[obfuscation_loops[-2][1]:obfuscation_loops[-1][0]] + statements + obfuscated_script[obfuscation_loops[-1][1] + 1:]
    
    return deobfuscated_script

# ========== Obfuscator 2 ----------
def replace_ACKNOWLEDGE(script):
    """
    Remplace toutes les chaines obfusquees par fonction :
    
    FUNC ACKNOWLEDGED ( $param1 , $param2 )
        $result = ""
        $obfuscated_string = StringSplit($param1 , "{" , 0x2 )
        FOR $index = 0 TO UBound($obfuscated_string)
            $result &= CHRW ( $obfuscated_string [ $index ] - $param2 )
        NEXT
        RETURN $result
    ENDFUNC
    """
    iNbReplaces = 0
    new_script = []
    i = 0
    for line in script:
        for m in re.searchiter(r'(.*)ACKNOWLEDGED \( \"([0-9{]+)\" , 0x([0-9a-f]+) \+ 0x([0-9a-f]+) \)(.*)', line, re.S):
            obfuscated_string = m.group(2)
            shift = (int(m.group(3), 16) + int(m.group(4), 16)) & 0xFFFFFFFF
            s = ""
            chars = obfuscated_string.split("{")
            for c in chars:
                # print(c, shift)
                s += chr(int(c)-shift)
            line = m.group(1) + "\"" + s + "\"" + m.group(5)
            iNbReplaces += 1
            print(f"'ACKNOWLEDGE ()' replaced by '{s}'")
        new_script.append(line)
        i += 1
        if i % 100 == 0:
            print(f"[i] line {i}")
    print(f"{iNbReplaces} Sqrt processed")
    return iNbReplaces, new_script

def simplify_WHILE_SWITCH(script):
    """
    """
    iNbReplaces = 0
    new_script = []
    num_line = 0
    while num_line <len(script):
        if re.search(r'WHILE 0x[0-9a-f]+.*', script[num_line])and \
           re.search(r'\$[A-Z]+ = 0x[0-9a-f]+.*', script[num_line+1])and \
           re.search(r'SWITCH \$[A-Z]+.*', script[num_line+2]) and \
           re.search(r'CASE 0x[0-9a-f]+.*', script[num_line+3]):
            print("found")
            # Look for the good CASE
            m = re.match(r'\$[A-Z].* = (0x[0-9a-f]+).*', script[num_line+1])
            case_value = m.group(1)
            l = num_line+4
            while script[l].find(f"CASE {m.group(1)}") != 0:
                l += 1
            deb_line = l+1
            # Look for EXITLOOP
            while script[l].find("EXITLOOP") != 0:
                l += 1
            end_line = l-1
            for l in range(deb_line, end_line+1):
                new_script.append(script[l])
            # look for WEND
            while script[l].find("WEND") != 0:
                l += 1
            num_line = l+1
            iNbReplaces += 1
            print(f"'WHILE SWITCK+H block' replaced")
        else:
            new_script.append(script[num_line])
            num_line += 1
    print(f"{iNbReplaces} WHILE SWITCH")
    return iNbReplaces, new_script

def remove_dead_code(script):
    """
    """
    iNbReplaces = 0
    new_script = []
    num_line = 0
    while num_line <len(script):
        if re.search(r'CEILING (.*', script[num_line]) or \
           re.search(r'CHR (.*', script[num_line]) or \
           re.search(r'COS (.*', script[num_line]) or \
           re.search(r'DIRGETSIZE (.*', script[num_line]) or \
           re.search(r'EXP (.*', script[num_line]) or \
           re.search(r'FLOOR (.*', script[num_line]) or \
           re.search(r'ISDECLARED (.*', script[num_line]) or \
           re.search(r'LOG (.*', script[num_line]) or \
           re.search(r'MEMGETSTATS (.*', script[num_line]) or \
           re.search(r'OBJGET (.*', script[num_line]) or \
           re.search(r'PIXELGETCOLOR (.*', script[num_line]) or \
           re.search(r'PROGRESSOFF (.*', script[num_line]):
            iNbReplaces += 1
            num_line += 1
        else:
            new_script.append(script[num_line])
            num_line += 1
    print(f"{iNbReplaces} lines deleted")
    return iNbReplaces, new_script

def beautify(script):
    indent = 0
    for line in script:
        if re.search(r'[ \t]*func .*', line.lower()) or \
           re.search(r'[ \t]*while[ \t\r\n]*', line.lower()) or \
           re.search(r'[ \t]*switch[ \t\r\n]*', line.lower()):
            indent += 1
        if re.search(r'[ \t]*endfunc[ \t\r\n]*', line.lower()) or \
           re.search(r'[ \t]*wend[ \t\r\n]*', line.lower()) or \
           re.search(r'[ \t]*endswitch[ \t\r\n]*', line.lower()):
            indent -= 1
        new_script.append(" "*4*indent + line.strip(" \t"))


"""
# Obfuscator 1
# ------------
n_shots_cleaners = [
group_multi_lines,
replace_globals_numerics,
replace_globals_functions_aliases,
replace_StringMid,
replace_StringReverse,
replace_StringTrimLeft,
replace_StringTrimRight,
replace_Asc,
replace_Chr,
replace_Sqrt,
replace_simples_bitrotates,
replace_bitnot,
replace_bitor,
replace_bitand,
replace_bitxor,
replace_minus_int,
replace_numeric_addition,
replace_numeric_soustraction,
replace_constants_arrays,
replace_two_dimensions_constants_arrays,
replace_string_concatenation,
# WARNING : this one will execute parts of AutoIt code !
# replace_constants_functions
]
"""

# Obfuscator 2
# ------------
# replace_ACKNOWLEDGE,
# remove_dead_code,
n_shots_cleaners = [
simplify_WHILE_SWITCH,
]

# read obfuscated script
with open(sys.argv[1], "rt") as f:
    script = f.readlines()

# apply one shot cleaners
'''
nb_grouped, script = group_multi_lines(script)
script = replace_globals_numerics(script)
script = replace_globals_functions_aliases(script)
nb_loops_deleted, script = delete_for_0_to_0_loops(script)
script = get_constants_arrays(script)
script = get_two_dimensions_constants_arrays(script)
nb_constants_functions, script = replace_constants_functions(script)
'''

# apply n shots cleaners
nb_passes = 1
while 1:
    print(f"pass {nb_passes} :")
    nb_hits = 0
    for function in n_shots_cleaners:
        nb, script = function(script)
        nb_hits += nb
    if nb_hits == 0:
        break
    nb_passes += 1
    
with open(f"{sys.argv[1]}.clean", "wt") as f:
    f.writelines(script)
