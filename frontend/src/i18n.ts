export type Language = "zh" | "en";

export type AppCopy = {
  language: {
    label: string;
    zh: string;
    en: string;
  };
  nav: {
    dashboard: string;
    config: string;
    papers: string;
    reports: string;
    delivery: string;
  };
  shell: {
    eyebrow: string;
    apiStatus: string;
  };
  common: {
    loadFailed: string;
    requestFailed: string;
    unclassified: string;
    matched: string;
    ok: string;
  };
  dashboard: {
    dailyRun: string;
    title: string;
    description: string;
    searchPapers: string;
    generateReport: string;
    sendToFeishu: string;
    statusEyebrow: string;
    states: {
      idle: string;
      running: string;
      done: string;
      error: string;
    };
    messages: {
      ready: string;
      working: string;
      searchDone: (count: number) => string;
      searchEmpty: string;
      reportGenerated: string;
      reportSent: string;
      warning: (warnings: string[]) => string;
    };
    keywordsEyebrow: string;
    keywordsTitle: string;
    keywordsDescription: string;
    venuesEyebrow: string;
    venuesTitle: string;
    venuesDescription: string;
  };
  config: {
    eyebrow: string;
    title: string;
    status: {
      loading: string;
      loaded: string;
      unsaved: string;
      saving: string;
      saved: string;
    };
    labels: {
      topicName: string;
      keywords: string;
      venues: string;
      excludeKeywords: string;
      lookbackDays: string;
      maxResults: string;
    };
    save: string;
  };
  papers: {
    loading: string;
    count: (count: number) => string;
    empty: string;
    eyebrow: string;
    refresh: string;
    columns: {
      title: string;
      venue: string;
      topics: string;
      match: string;
    };
  };
  reports: {
    loading: string;
    count: (count: number) => string;
    empty: string;
    sending: string;
    sent: string;
    eyebrow: string;
    sendReport: (title: string) => string;
  };
  delivery: {
    notTested: string;
    sending: string;
    sent: (messageId: string) => string;
    failed: string;
    eyebrow: string;
    title: string;
    sendTest: string;
  };
};

export const copy: Record<Language, AppCopy> = {
  zh: {
    language: {
      label: "语言",
      zh: "中文",
      en: "English"
    },
    nav: {
      dashboard: "仪表盘",
      config: "配置",
      papers: "论文",
      reports: "报告",
      delivery: "飞书"
    },
    shell: {
      eyebrow: "本地研究监控",
      apiStatus: "FastAPI: 127.0.0.1:8000"
    },
    common: {
      loadFailed: "加载失败",
      requestFailed: "请求失败。",
      unclassified: "未分类",
      matched: "已匹配",
      ok: "ok"
    },
    dashboard: {
      dailyRun: "每日运行",
      title: "生成今天的研究简报",
      description: "按已配置主题查找论文，汇总匹配结果，并发送报告到飞书。",
      searchPapers: "查找论文",
      generateReport: "生成报告",
      sendToFeishu: "发送到飞书",
      statusEyebrow: "投递状态",
      states: {
        idle: "就绪",
        running: "运行中",
        done: "已完成",
        error: "需要处理"
      },
      messages: {
        ready: "本地工作流已就绪。",
        working: "处理中...",
        searchDone: (count) => `找到 ${count} 篇论文，可到论文页查看。`,
        searchEmpty: "没有找到匹配论文。请检查配置页里的关键词、会议/期刊和时间范围。",
        reportGenerated: "报告已生成。",
        reportSent: "报告已发送到飞书。",
        warning: (warnings) => `警告：${warnings.join("; ")}`
      },
      keywordsEyebrow: "关键词",
      keywordsTitle: "在配置页管理",
      keywordsDescription: "建议保持主题名称简短，每行一个关键词，匹配结果会更稳定。",
      venuesEyebrow: "会议/期刊",
      venuesTitle: "会议和期刊过滤",
      venuesDescription: "可使用 ICLR、NeurIPS、ACL、EMNLP、Nature Machine Intelligence 等名称。"
    },
    config: {
      eyebrow: "配置",
      title: "主题和来源匹配",
      status: {
        loading: "正在加载...",
        loaded: "已加载",
        unsaved: "未保存的本地修改",
        saving: "保存中...",
        saved: "已保存"
      },
      labels: {
        topicName: "主题名称",
        keywords: "关键词",
        venues: "会议/期刊",
        excludeKeywords: "排除关键词",
        lookbackDays: "回溯天数",
        maxResults: "每个来源最多结果数"
      },
      save: "保存配置"
    },
    papers: {
      loading: "正在加载论文...",
      count: (count) => `${count} 篇论文`,
      empty: "还没有论文",
      eyebrow: "最近匹配",
      refresh: "刷新论文",
      columns: {
        title: "标题",
        venue: "会议/期刊",
        topics: "主题",
        match: "匹配原因"
      }
    },
    reports: {
      loading: "正在加载报告...",
      count: (count) => `${count} 份报告`,
      empty: "还没有报告",
      sending: "发送中...",
      sent: "报告已发送",
      eyebrow: "最新报告",
      sendReport: (title) => `发送 ${title}`
    },
    delivery: {
      notTested: "尚未测试",
      sending: "正在发送测试消息...",
      sent: (messageId) => `已发送：${messageId}`,
      failed: "投递测试失败",
      eyebrow: "投递状态",
      title: "飞书私聊消息",
      sendTest: "发送测试消息"
    }
  },
  en: {
    language: {
      label: "Language",
      zh: "中文",
      en: "English"
    },
    nav: {
      dashboard: "Dashboard",
      config: "Config",
      papers: "Papers",
      reports: "Reports",
      delivery: "Feishu"
    },
    shell: {
      eyebrow: "Local research monitor",
      apiStatus: "FastAPI: 127.0.0.1:8000"
    },
    common: {
      loadFailed: "Load failed",
      requestFailed: "Request failed.",
      unclassified: "unclassified",
      matched: "matched",
      ok: "ok"
    },
    dashboard: {
      dailyRun: "Daily run",
      title: "Generate today's research brief",
      description: "Search configured topics, summarize matched papers, and deliver the report to Feishu.",
      searchPapers: "Search papers",
      generateReport: "Generate report",
      sendToFeishu: "Send to Feishu",
      statusEyebrow: "Delivery status",
      states: {
        idle: "Ready",
        running: "Running",
        done: "Completed",
        error: "Needs attention"
      },
      messages: {
        ready: "Local workflow is ready.",
        working: "Working...",
        searchDone: (count) => `${count} papers found. Open the Papers page to review them.`,
        searchEmpty: "No matching papers found. Check the keywords, venues, and lookback window on the Config page.",
        reportGenerated: "Report generated.",
        reportSent: "Report sent to Feishu.",
        warning: (warnings) => `Warning: ${warnings.join("; ")}`
      },
      keywordsEyebrow: "Keywords",
      keywordsTitle: "Configured in the Config page",
      keywordsDescription: "Keep topic names short and put one keyword per line for predictable matching.",
      venuesEyebrow: "Venues",
      venuesTitle: "Conference and journal filters",
      venuesDescription: "Use names like ICLR, NeurIPS, ACL, EMNLP, Nature Machine Intelligence."
    },
    config: {
      eyebrow: "Config",
      title: "Topic and source matching",
      status: {
        loading: "Loading...",
        loaded: "Loaded",
        unsaved: "Unsaved local edits",
        saving: "Saving...",
        saved: "Saved"
      },
      labels: {
        topicName: "Topic name",
        keywords: "Keywords",
        venues: "Venues",
        excludeKeywords: "Exclude keywords",
        lookbackDays: "Lookback days",
        maxResults: "Max results per source"
      },
      save: "Save config"
    },
    papers: {
      loading: "Loading papers...",
      count: (count) => `${count} papers`,
      empty: "No papers yet",
      eyebrow: "Recent matches",
      refresh: "Refresh papers",
      columns: {
        title: "Title",
        venue: "Venue",
        topics: "Topics",
        match: "Match"
      }
    },
    reports: {
      loading: "Loading reports...",
      count: (count) => `${count} reports`,
      empty: "No reports yet",
      sending: "Sending...",
      sent: "Report sent",
      eyebrow: "Latest report",
      sendReport: (title) => `Send ${title}`
    },
    delivery: {
      notTested: "Not tested",
      sending: "Sending test message...",
      sent: (messageId) => `Sent: ${messageId}`,
      failed: "Delivery test failed",
      eyebrow: "Delivery status",
      title: "Feishu private message",
      sendTest: "Send test message"
    }
  }
};
