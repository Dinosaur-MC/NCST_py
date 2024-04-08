import sys
import os
import re

VERSION = "1.1"


def main():
    # 解析命令行参数
    if len(sys.argv) != 3:
        if len(sys.argv) == 2 and sys.argv[1] == "-v":
            print(
                "[Number Checking & Standardization Tool by Dinosaur_MC]\nVersion:",
                VERSION,
            )
            return 0
        print("Usage: python3 " + sys.argv[0] + " <config> <dir_path>")
        return 1

    names_path = sys.argv[1]
    dir_path = sys.argv[2]

    # 读取名册
    with open(names_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

        formatter = lines[0][0:-1]
        header_line = lines[1].strip()
        item_lines = [x.strip() for x in lines[2:]]

        headers = [x.strip() for x in header_line.split(" ")]
        items = []
        for item in item_lines:
            i = item.split(" ")
            if len(i) == len(headers) and i not in items:
                items.append(i)

    # 打印配置
    print("========== [Config] ==========")
    print("Scan Path:", os.path.abspath(dir_path), sep="\n\t")
    print("Formatter:", formatter, sep="\n\t")
    print("Headers:", "\t".join(headers), sep="\n\t")
    print(
        "Items ({}):".format(len(items)),
        "\n\t".join(["\t".join(x) for x in items]),
        sep="\n\t",
    )

    # 扫描目录文件
    with os.scandir(dir_path) as entrys:
        files = []
        for entry in entrys:
            if entry.is_file():
                # 分离扩展名
                m = re.match(".*(\\..*$)", entry.name)
                if m:
                    files.append((entry.name[0 : -len(m.group(1))], m.group(1)))
                else:
                    files.append((entry.name, ""))

    # 匹配项目
    targets = []
    cur_items = list(files)
    matched = []
    fuzzy_matched = []
    for item in items:
        # 生成标准化目标（变量替换）
        raw_target = formatter
        for i in range(len(headers)):
            raw_target = raw_target.replace("$" + headers[i] + "$", item[i])
        # 分离扩展名
        m = re.match(".*(\\..*$)", raw_target)
        if m:
            target = (raw_target[0 : -len(m.group(1))], m.group(1))
        else:
            target = (raw_target, "")
        targets.append(target)

        # 精准匹配项目
        for cur_item in cur_items:
            if (cur_item == target) or (cur_item[0] == target[0] and target[1] == ".*"):
                matched.append(("".join(cur_item)))
                cur_items.remove(cur_item)
                targets.remove(target)
                break

        # 模糊匹配项目
        for cur_item in cur_items:
            if (cur_item[1] == target[1] or target[1] == ".*") and (
                [True] * len(headers)
                == [re.match(".*?{}.*?".format(x), cur_item[0]) != None for x in item]
            ):
                fuzzy_matched.append(
                    ("".join(cur_item), target[0] + cur_item[1], target)
                )
                cur_items.remove(cur_item)
                break
    unmatched = list(set(["".join(x) for x in files]) - set(matched))
    missing = list(set(["".join(x) for x in targets]))

    # 输出匹配结果
    print("========== [Matching Result] ==========")
    print(
        "Matched ({}):".format(len(matched)),
        "\n\t".join(matched),
        sep="\n\t",
    )
    print(
        "Fuzzy Matched ({}):".format(len(fuzzy_matched)),
        "\n\t".join(["\t->\t".join(x[0:2]) for x in fuzzy_matched]),
        sep="\n\t",
    )
    print("Unmatched ({}):".format(len(unmatched)), "\n\t".join(unmatched), sep="\n\t")
    print("Missing ({}):".format(len(missing)), "\n\t".join(missing), sep="\n\t")

    # 标准化模糊结果
    print("========== [Operation] ==========")
    if len(fuzzy_matched) > 0:
        comfirm = input(
            "Standardizable item has found ({}), do you want to fix it? (Y/n): ".format(
                len(fuzzy_matched)
            )
        )
        if (comfirm.lower() == "y") or (comfirm.lower() != "n" and comfirm == ""):
            for x in fuzzy_matched:
                os.rename(os.path.join(dir_path, x[0]), os.path.join(dir_path, x[1]))
                targets.remove(x[2])
                unmatched.remove(x[0])
                print("\t" + x[0] + "\t->\t" + x[1])
            print("Done!")
        else:
            print("Canceled.")
    else:
        print("No standardizable item has found.")

    # 处理未匹配的项目
    print("========== [Operation] ==========")
    if len(unmatched) > 0:
        comfirm = input(
            "Unmatched item has found ({}), do you want to move it to another place? (Y/n): ".format(
                len(unmatched)
            )
        )
        if (comfirm.lower() == "y") or (comfirm.lower() != "n" and comfirm == ""):
            bak_path = input("Please enter the path you wish to move to (.\\backup):")
            if bak_path == "":
                bak_path = ".\\backup"
            if not os.path.exists(bak_path):
                os.mkdir(bak_path)
                print("Created directory:", bak_path)
            flag = True
            for x in unmatched:
                if not os.path.exists(os.path.join(bak_path, x)):
                    os.rename(os.path.join(dir_path, x), os.path.join(bak_path, x))
                    print("\t" + os.path.join(dir_path, x) + "\t->\t" + os.path.join(bak_path, x))
                else:
                    print("\t" + os.path.join(bak_path, x) + " already exists")
                    flag = False
            if flag:
                print("Done!")
            else:
                print("Done, but some problem occurred!")
        else:
            print("Canceled.")
    else:
        print("No unmatched item has found.")

    # 输出最终结果
    print("========== [Final Result] ==========")
    if len(matched) == len(items):
        print("Great! All items have been matched!")
    else:
        missing = list(set(["".join(x) for x in targets]))
        print("Sorry, {} item(s) have not been matched:".format(len(missing)))
        print("\t" + "\n\t".join(missing))
    print(
        "Matched: {} of total {} ({:.2f}%)".format(
            len(matched), len(items), len(matched) / len(items) * 100.0
        )
    )

    return 0


if __name__ == "__main__":
    main()
