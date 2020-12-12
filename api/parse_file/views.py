from api.parse_file.pdf import extract_text_from_pdf


def dnk_covid(file_data):
    prefixes = []
    A = [f"A{i}" for i in range(1, 13)]
    prefixes.extend(A)
    B = [f"B{i}" for i in range(1, 13)]
    prefixes.extend(B)
    C = [f"C{i}" for i in range(1, 13)]
    prefixes.extend(C)
    D = [f"D{i}" for i in range(1, 13)]
    prefixes.extend(D)
    E = [f"E{i}" for i in range(1, 13)]
    prefixes.extend(E)
    F = [f"F{i}" for i in range(1, 13)]
    prefixes.extend(F)
    G = [f"G{i}" for i in range(1, 13)]
    prefixes.extend(G)
    H = [f"H{i}" for i in range(1, 13)]
    prefixes.extend(H)
    I = [f"I{i}" for i in range(1, 13)]
    prefixes.extend(I)
    J = [f"J{i}" for i in range(1, 13)]
    prefixes.extend(J)
    K = [f"K{i}" for i in range(1, 13)]
    prefixes.extend(K)

    t = extract_text_from_pdf(file_data).replace("\n", "").split("Коронавирусы подобные SARS-CoVВККоронавирус SARS-CoV-2")
    for i in t:
        if "+" in i:
            k = i.split("N")
            if k[1].split(" ")[0].isdigit():
                return {"pk": k[1].split(" ")[0], "result": "Положительно"}
        else:
            k = i.split("N")
            if k[1].split(" ")[0].isdigit():
                return {"pk": k[1].split(" ")[0], "result": "Отрицательно"}
