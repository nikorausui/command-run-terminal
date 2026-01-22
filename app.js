const connections = {
  rdp: {
    title: "RDP (ユーザー端末 → 管理端末)",
    description: "横展開の主要経路。認証の成否・セッション生成・プロセス起動をセットで確認します。",
    bullets: [
      "セキュリティログ: 4624 (LogonType 10/3), 4625, 4778, 4779",
      "プロセス: mstsc.exe からの起動履歴, 4688, Sysmon Event ID 1",
      "怪しい挙動: 深夜帯/地理的に不自然なIP, 短時間の連続失敗",
      "NLA無効・古い暗号スイートの使用",
    ],
  },
  "rdp-admin": {
    title: "RDP (管理端末 → 開発端末)",
    description: "管理端末の資格情報が使用されるため、特権アカウントの利用状況を重視します。",
    bullets: [
      "ログ: 4624 (Privileged), 4672, 4688 (runas/PSExecなど)",
      "セッション中の権限昇格や資格情報ダンプの兆候",
      "EDRでの横展開検知アラートの有無",
    ],
  },
  kerberos: {
    title: "Kerberos (PC → ADサーバ)",
    description: "チケット要求と認証の異常を検知することが重要です。",
    bullets: [
      "KDCログ: 4768, 4769, 4771 (失敗理由も確認)",
      "AS-REP RoastingやService Ticketの大量取得",
      "異常な暗号方式や未知端末からのリクエスト",
    ],
  },
  powershell: {
    title: "PowerShell Remoting (PC → ADサーバ)",
    description: "スクリプトの内容とリモート実行経路を確認します。",
    bullets: [
      "PowerShell 4103/4104 (スクリプトブロックログ)",
      "WinRMの接続ログ、4688 (powershell.exe)",
      "Invoke-Command / New-PSSession の利用状況",
      "難読化やダウンロード実行 (IEX, Base64)",
    ],
  },
  ldap: {
    title: "LDAP (PC → ADサーバ)",
    description: "AD探索や大量クエリの兆候を検知します。",
    bullets: [
      "Directory Service: 1644 (LDAPクエリログ)",
      "BloodHound/SharpHoundなどの探索パターン",
      "短時間での大規模なグループ列挙",
    ],
  },
  smb: {
    title: "SMB (ADサーバ → ファイルサーバ)",
    description: "共有アクセスや資格情報の横展開を追跡します。",
    bullets: [
      "ログ: 4624 (LogonType 3), 5140 (共有アクセス)",
      "ADMIN$やC$へのアクセス頻度",
      "ransomware実行前の暗号化テストファイル",
      "SMB署名の無効化や古いSMBv1の使用",
    ],
  },
};

const modal = document.getElementById("modal");
const modalTitle = document.getElementById("modal-title");
const modalBody = document.getElementById("modal-body");

const openModal = (connectionKey) => {
  const details = connections[connectionKey];
  if (!details) {
    return;
  }

  modalTitle.textContent = details.title;
  modalBody.innerHTML = `
    <p>${details.description}</p>
    <ul>${details.bullets.map((item) => `<li>${item}</li>`).join("")}</ul>
  `;
  modal.setAttribute("aria-hidden", "false");
};

const closeModal = () => {
  modal.setAttribute("aria-hidden", "true");
};

const buttons = document.querySelectorAll(".edge-button");
buttons.forEach((button) => {
  button.addEventListener("click", () => {
    openModal(button.dataset.connection);
  });
});

modal.addEventListener("click", (event) => {
  if (event.target instanceof HTMLElement && event.target.dataset.close === "true") {
    closeModal();
  }
});

document.addEventListener("keydown", (event) => {
  if (event.key === "Escape") {
    closeModal();
  }
});
