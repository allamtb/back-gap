namespace FuturesTradeViewer
{
    partial class MainForm
    {
        private System.ComponentModel.IContainer components = null;
        private DataGridView tradeGrid;
        private DataGridView buyGrid;
        private DataGridView sellGrid;
        private Button connectButton;
        private TextBox symbolBox;
        private Label label1;
        private CheckBox useProxyCheckBox;
        private TextBox proxyTextBox;
        private Label tradeTitleLabel;
        private Label orderTitleLabel;
        private Label buyTitleLabel;
        private Label sellTitleLabel;
        private Label connectionStatusLabel; // 连接状态标签
        private Button viewStatisticsButton; // 查看市价比统计文件按钮
        private Button viewLargeOrderStatisticsButton; // 查看大单统计文件按钮
        private Button viewAbnormalDetailButton; // 查看异常大单监控明细按钮
        private ComboBox priceTickComboBox; // 价格精度选择器
        
        // 异常大单监控控件
        private GroupBox abnormalGroupBox;
        private Label windowLabel;
        private ComboBox windowComboBox;
        private Label multipleLabel;
        private NumericUpDown multipleNumeric;
        private Label thresholdLabel;
        private NumericUpDown thresholdNumeric;
        private CheckBox onlyActiveTakerCheckBox;
        private Panel statsPanel;
        private Label statsShortTermLabel;
        private Label statsLongTermLabel;
        private Label statsBuyAbnormalLabel;
        private Label statsSellAbnormalLabel;
        private Label statsDirectionLabel;
        private DataGridView abnormalGrid;

        // 连续大单监控控件
        private GroupBox consecutiveGroupBox;
        private CheckBox enableConsecutiveCheckBox;
        private Label consecutiveWindowLabel;
        private ComboBox consecutiveWindowComboBox;
        private Label consecutiveCountLabel;
        private NumericUpDown consecutiveCountNumeric;
        private Label consecutiveThresholdLabel;
        private NumericUpDown consecutiveThresholdNumeric;
        private CheckBox consecutiveSameDirectionCheckBox;
        private Panel consecutiveStatsPanel;
        private Label consecutiveBuyCountLabel;
        private Label consecutiveBuyVolumeLabel;
        private Label consecutiveBuyStatusLabel;
        private Label consecutiveSellCountLabel;
        private Label consecutiveSellVolumeLabel;
        private Label consecutiveSellStatusLabel;
        private DataGridView consecutiveHistoryGrid;

        protected override void Dispose(bool disposing)
        {
            if (disposing)
            {
                // 停止定时器
                statsUpdateTimer?.Stop();
                statsUpdateTimer?.Dispose();

                // 释放 WebSocket 连接
                webSocketManager?.Dispose();

                // 释放其他托管资源
                if (components != null) components.Dispose();
            }
            base.Dispose(disposing);
        }

        private void InitializeComponent()
        {
            tradeGrid = new DataGridView();
            buyGrid = new DataGridView();
            sellGrid = new DataGridView();
            connectButton = new Button();
            symbolBox = new TextBox();
            label1 = new Label();
            useProxyCheckBox = new CheckBox();
            proxyTextBox = new TextBox();
            tradeTitleLabel = new Label();
            orderTitleLabel = new Label();
            buyTitleLabel = new Label();
            sellTitleLabel = new Label();
            abnormalGroupBox = new GroupBox();
            windowLabel = new Label();
            windowComboBox = new ComboBox();
            multipleLabel = new Label();
            multipleNumeric = new NumericUpDown();
            thresholdLabel = new Label();
            thresholdNumeric = new NumericUpDown();
            onlyActiveTakerCheckBox = new CheckBox();
            statsPanel = new Panel();
            statsShortTermLabel = new Label();
            statsLongTermLabel = new Label();
            statsBuyAbnormalLabel = new Label();
            statsSellAbnormalLabel = new Label();
            statsDirectionLabel = new Label();
            abnormalGrid = new DataGridView();
            consecutiveGroupBox = new GroupBox();
            enableConsecutiveCheckBox = new CheckBox();
            consecutiveWindowLabel = new Label();
            consecutiveWindowComboBox = new ComboBox();
            consecutiveCountLabel = new Label();
            consecutiveCountNumeric = new NumericUpDown();
            consecutiveThresholdLabel = new Label();
            consecutiveThresholdNumeric = new NumericUpDown();
            consecutiveSameDirectionCheckBox = new CheckBox();
            consecutiveStatsPanel = new Panel();
            consecutiveBuyCountLabel = new Label();
            consecutiveBuyVolumeLabel = new Label();
            consecutiveBuyStatusLabel = new Label();
            consecutiveSellCountLabel = new Label();
            consecutiveSellVolumeLabel = new Label();
            consecutiveSellStatusLabel = new Label();
            consecutiveHistoryGrid = new DataGridView();
            connectionStatusLabel = new Label();
            viewStatisticsButton = new Button();
            viewLargeOrderStatisticsButton = new Button();
            viewAbnormalDetailButton = new Button();
            priceTickComboBox = new ComboBox();
            ((System.ComponentModel.ISupportInitialize)tradeGrid).BeginInit();
            ((System.ComponentModel.ISupportInitialize)buyGrid).BeginInit();
            ((System.ComponentModel.ISupportInitialize)sellGrid).BeginInit();
            abnormalGroupBox.SuspendLayout();
            ((System.ComponentModel.ISupportInitialize)multipleNumeric).BeginInit();
            ((System.ComponentModel.ISupportInitialize)thresholdNumeric).BeginInit();
            statsPanel.SuspendLayout();
            ((System.ComponentModel.ISupportInitialize)abnormalGrid).BeginInit();
            consecutiveGroupBox.SuspendLayout();
            ((System.ComponentModel.ISupportInitialize)consecutiveCountNumeric).BeginInit();
            ((System.ComponentModel.ISupportInitialize)consecutiveThresholdNumeric).BeginInit();
            consecutiveStatsPanel.SuspendLayout();
            ((System.ComponentModel.ISupportInitialize)consecutiveHistoryGrid).BeginInit();
            SuspendLayout();
            // 
            // tradeGrid
            // 
            tradeGrid.AllowUserToAddRows = false;
            tradeGrid.AllowUserToDeleteRows = false;
            tradeGrid.Anchor = AnchorStyles.Top | AnchorStyles.Bottom | AnchorStyles.Left;
            tradeGrid.ColumnHeadersHeightSizeMode = DataGridViewColumnHeadersHeightSizeMode.AutoSize;
            tradeGrid.Location = new Point(758, 112);
            tradeGrid.Name = "tradeGrid";
            tradeGrid.ReadOnly = true;
            tradeGrid.RowHeadersWidth = 62;
            tradeGrid.Size = new Size(487, 170);
            tradeGrid.TabIndex = 4;
            // 
            // buyGrid
            // 
            buyGrid.AllowUserToAddRows = false;
            buyGrid.AllowUserToDeleteRows = false;
            buyGrid.Anchor = AnchorStyles.Bottom | AnchorStyles.Left;
            buyGrid.ColumnHeadersHeightSizeMode = DataGridViewColumnHeadersHeightSizeMode.AutoSize;
            buyGrid.Location = new Point(315, 112);
            buyGrid.Name = "buyGrid";
            buyGrid.ReadOnly = true;
            buyGrid.RowHeadersWidth = 62;
            buyGrid.Size = new Size(261, 170);
            buyGrid.TabIndex = 6;
            // 
            // sellGrid
            // 
            sellGrid.AllowUserToAddRows = false;
            sellGrid.AllowUserToDeleteRows = false;
            sellGrid.Anchor = AnchorStyles.Top | AnchorStyles.Bottom | AnchorStyles.Left;
            sellGrid.ColumnHeadersHeightSizeMode = DataGridViewColumnHeadersHeightSizeMode.AutoSize;
            sellGrid.Location = new Point(45, 112);
            sellGrid.Name = "sellGrid";
            sellGrid.ReadOnly = true;
            sellGrid.RowHeadersWidth = 62;
            sellGrid.Size = new Size(247, 170);
            sellGrid.TabIndex = 5;
            // 
            // connectButton
            // 
            connectButton.Location = new Point(453, 8);
            connectButton.Name = "connectButton";
            connectButton.Size = new Size(172, 49);
            connectButton.TabIndex = 2;
            connectButton.Text = "点击连接";
            connectButton.UseVisualStyleBackColor = true;
            connectButton.Click += ConnectButton_Click;
            // 
            // symbolBox
            // 
            symbolBox.Location = new Point(95, 17);
            symbolBox.Name = "symbolBox";
            symbolBox.Size = new Size(77, 23);
            symbolBox.TabIndex = 1;
            symbolBox.Text = "btcusdt";
            // 
            // label1
            // 
            label1.Location = new Point(20, 20);
            label1.Name = "label1";
            label1.Size = new Size(69, 23);
            label1.TabIndex = 0;
            label1.Text = "币种：";
            label1.Click += label1_Click;
            // 
            // useProxyCheckBox
            // 
            useProxyCheckBox.Checked = true;
            useProxyCheckBox.CheckState = CheckState.Checked;
            useProxyCheckBox.Location = new Point(202, 12);
            useProxyCheckBox.Name = "useProxyCheckBox";
            useProxyCheckBox.Size = new Size(75, 31);
            useProxyCheckBox.TabIndex = 3;
            useProxyCheckBox.Text = "使用代理";
            // 
            // proxyTextBox
            // 
            proxyTextBox.Location = new Point(300, 17);
            proxyTextBox.Name = "proxyTextBox";
            proxyTextBox.Size = new Size(137, 23);
            proxyTextBox.TabIndex = 7;
            proxyTextBox.Text = "http://127.0.0.1:1080";
            // 
            // tradeTitleLabel
            // 
            tradeTitleLabel.Font = new Font("Microsoft YaHei UI", 10F, FontStyle.Bold);
            tradeTitleLabel.ForeColor = Color.DarkBlue;
            tradeTitleLabel.Location = new Point(928, 91);
            tradeTitleLabel.Name = "tradeTitleLabel";
            tradeTitleLabel.Size = new Size(91, 18);
            tradeTitleLabel.TabIndex = 8;
            tradeTitleLabel.Text = "实时成交";
            // 
            // orderTitleLabel
            // 
            orderTitleLabel.Font = new Font("Microsoft YaHei UI", 10F, FontStyle.Bold);
            orderTitleLabel.ForeColor = Color.DarkSlateGray;
            orderTitleLabel.Location = new Point(215, 65);
            orderTitleLabel.Name = "orderTitleLabel";
            orderTitleLabel.Size = new Size(250, 20);
            orderTitleLabel.TabIndex = 9;
            orderTitleLabel.Text = "委托订单";
            orderTitleLabel.Click += orderTitleLabel_Click;
            // 
            // buyTitleLabel
            // 
            buyTitleLabel.Font = new Font("Microsoft YaHei UI", 9F, FontStyle.Bold);
            buyTitleLabel.ForeColor = Color.DarkGreen;
            buyTitleLabel.Location = new Point(365, 86);
            buyTitleLabel.Name = "buyTitleLabel";
            buyTitleLabel.Size = new Size(100, 17);
            buyTitleLabel.TabIndex = 11;
            buyTitleLabel.Text = "买单(BID)";
            // 
            // sellTitleLabel
            // 
            sellTitleLabel.Font = new Font("Microsoft YaHei UI", 9F, FontStyle.Bold);
            sellTitleLabel.ForeColor = Color.DarkRed;
            sellTitleLabel.Location = new Point(95, 91);
            sellTitleLabel.Name = "sellTitleLabel";
            sellTitleLabel.Size = new Size(110, 18);
            sellTitleLabel.TabIndex = 10;
            sellTitleLabel.Text = "卖单(ASK)";
            // 
            // abnormalGroupBox
            // 
            abnormalGroupBox.Anchor = AnchorStyles.Bottom | AnchorStyles.Left;
            abnormalGroupBox.Controls.Add(windowLabel);
            abnormalGroupBox.Controls.Add(windowComboBox);
            abnormalGroupBox.Controls.Add(multipleLabel);
            abnormalGroupBox.Controls.Add(multipleNumeric);
            abnormalGroupBox.Controls.Add(thresholdLabel);
            abnormalGroupBox.Controls.Add(thresholdNumeric);
            abnormalGroupBox.Controls.Add(onlyActiveTakerCheckBox);
            abnormalGroupBox.Controls.Add(statsPanel);
            abnormalGroupBox.Controls.Add(abnormalGrid);
            abnormalGroupBox.Font = new Font("Microsoft YaHei UI", 9F, FontStyle.Bold);
            abnormalGroupBox.ForeColor = Color.DarkRed;
            abnormalGroupBox.Location = new Point(12, 298);
            abnormalGroupBox.Name = "abnormalGroupBox";
            abnormalGroupBox.Size = new Size(740, 546);
            abnormalGroupBox.TabIndex = 12;
            abnormalGroupBox.TabStop = false;
            abnormalGroupBox.Text = "【异常大单】";
            // 
            // windowLabel
            // 
            windowLabel.Font = new Font("Microsoft YaHei UI", 9F);
            windowLabel.Location = new Point(20, 31);
            windowLabel.Name = "windowLabel";
            windowLabel.Size = new Size(90, 23);
            windowLabel.TabIndex = 1;
            windowLabel.Text = "时间窗口：";
            // 
            // windowComboBox
            // 
            windowComboBox.DropDownStyle = ComboBoxStyle.DropDownList;
            windowComboBox.Font = new Font("Microsoft YaHei UI", 9F);
            windowComboBox.FormattingEnabled = true;
            windowComboBox.Items.AddRange(new object[] { "1分钟", "3分钟", "5分钟", "10分钟" });
            windowComboBox.Location = new Point(110, 28);
            windowComboBox.Name = "windowComboBox";
            windowComboBox.Size = new Size(80, 25);
            windowComboBox.TabIndex = 2;
            // 
            // multipleLabel
            // 
            multipleLabel.Font = new Font("Microsoft YaHei UI", 9F);
            multipleLabel.Location = new Point(200, 31);
            multipleLabel.Name = "multipleLabel";
            multipleLabel.Size = new Size(90, 23);
            multipleLabel.TabIndex = 3;
            multipleLabel.Text = "异常倍数：";
            // 
            // multipleNumeric
            // 
            multipleNumeric.DecimalPlaces = 1;
            multipleNumeric.Font = new Font("Microsoft YaHei UI", 9F);
            multipleNumeric.Increment = new decimal(new int[] { 5, 0, 0, 65536 });
            multipleNumeric.Location = new Point(290, 28);
            multipleNumeric.Maximum = new decimal(new int[] { 20, 0, 0, 0 });
            multipleNumeric.Minimum = new decimal(new int[] { 15, 0, 0, 65536 });
            multipleNumeric.Name = "multipleNumeric";
            multipleNumeric.Size = new Size(70, 23);
            multipleNumeric.TabIndex = 4;
            multipleNumeric.Value = new decimal(new int[] { 25, 0, 0, 65536 });
            // 
            // thresholdLabel
            // 
            thresholdLabel.Font = new Font("Microsoft YaHei UI", 9F);
            thresholdLabel.Location = new Point(370, 31);
            thresholdLabel.Name = "thresholdLabel";
            thresholdLabel.Size = new Size(100, 23);
            thresholdLabel.TabIndex = 5;
            thresholdLabel.Text = "最小量阈值：";
            // 
            // thresholdNumeric
            // 
            thresholdNumeric.DecimalPlaces = 2;
            thresholdNumeric.Font = new Font("Microsoft YaHei UI", 9F);
            thresholdNumeric.Increment = new decimal(new int[] { 1, 0, 0, 65536 });
            thresholdNumeric.Location = new Point(470, 28);
            thresholdNumeric.Minimum = new decimal(new int[] { 1, 0, 0, 131072 });
            thresholdNumeric.Name = "thresholdNumeric";
            thresholdNumeric.Size = new Size(80, 23);
            thresholdNumeric.TabIndex = 6;
            thresholdNumeric.Value = new decimal(new int[] { 5, 0, 0, 65536 });
            // 
            // onlyActiveTakerCheckBox
            // 
            onlyActiveTakerCheckBox.Font = new Font("Microsoft YaHei UI", 9F);
            onlyActiveTakerCheckBox.Location = new Point(570, 30);
            onlyActiveTakerCheckBox.Name = "onlyActiveTakerCheckBox";
            onlyActiveTakerCheckBox.Size = new Size(180, 24);
            onlyActiveTakerCheckBox.TabIndex = 7;
            onlyActiveTakerCheckBox.Text = "只显示主动吃单";
            onlyActiveTakerCheckBox.Visible = false;
            // 
            // statsPanel
            // 
            statsPanel.BackColor = Color.FromArgb(240, 248, 255);
            statsPanel.BorderStyle = BorderStyle.FixedSingle;
            statsPanel.Controls.Add(statsShortTermLabel);
            statsPanel.Controls.Add(statsLongTermLabel);
            statsPanel.Controls.Add(statsBuyAbnormalLabel);
            statsPanel.Controls.Add(statsSellAbnormalLabel);
            statsPanel.Controls.Add(statsDirectionLabel);
            statsPanel.Location = new Point(10, 60);
            statsPanel.Name = "statsPanel";
            statsPanel.Size = new Size(720, 59);
            statsPanel.TabIndex = 8;
            // 
            // statsShortTermLabel
            // 
            statsShortTermLabel.Font = new Font("Microsoft YaHei UI", 9F);
            statsShortTermLabel.ForeColor = Color.Black;
            statsShortTermLabel.Location = new Point(10, 5);
            statsShortTermLabel.Name = "statsShortTermLabel";
            statsShortTermLabel.Size = new Size(263, 23);
            statsShortTermLabel.TabIndex = 0;
            statsShortTermLabel.Text = "短期(5分钟)：平均 0.00 BTC/笔 | 总笔数：0笔";
            // 
            // statsLongTermLabel
            // 
            statsLongTermLabel.Font = new Font("Microsoft YaHei UI", 9F);
            statsLongTermLabel.ForeColor = Color.Black;
            statsLongTermLabel.Location = new Point(10, 28);
            statsLongTermLabel.Name = "statsLongTermLabel";
            statsLongTermLabel.Size = new Size(261, 23);
            statsLongTermLabel.TabIndex = 1;
            statsLongTermLabel.Text = "长期(30分钟)：平均 0.00 BTC/笔 | 总笔数：0笔";
            // 
            // statsBuyAbnormalLabel
            // 
            statsBuyAbnormalLabel.Font = new Font("Microsoft YaHei UI", 9F);
            statsBuyAbnormalLabel.ForeColor = Color.DarkGreen;
            statsBuyAbnormalLabel.Location = new Point(277, 5);
            statsBuyAbnormalLabel.Name = "statsBuyAbnormalLabel";
            statsBuyAbnormalLabel.Size = new Size(182, 23);
            statsBuyAbnormalLabel.TabIndex = 3;
            statsBuyAbnormalLabel.Text = "买入大单：0笔(0.00 BTC) \U0001f7e2";
            // 
            // statsSellAbnormalLabel
            // 
            statsSellAbnormalLabel.Font = new Font("Microsoft YaHei UI", 9F);
            statsSellAbnormalLabel.ForeColor = Color.DarkRed;
            statsSellAbnormalLabel.Location = new Point(279, 28);
            statsSellAbnormalLabel.Name = "statsSellAbnormalLabel";
            statsSellAbnormalLabel.Size = new Size(180, 23);
            statsSellAbnormalLabel.TabIndex = 4;
            statsSellAbnormalLabel.Text = "卖出大单：0笔(0.00 BTC) 🔴";
            // 
            // statsDirectionLabel
            // 
            statsDirectionLabel.Font = new Font("Microsoft YaHei UI", 10F, FontStyle.Bold);
            statsDirectionLabel.ForeColor = Color.DarkSlateGray;
            statsDirectionLabel.Location = new Point(465, 16);
            statsDirectionLabel.Name = "statsDirectionLabel";
            statsDirectionLabel.Size = new Size(205, 23);
            statsDirectionLabel.TabIndex = 5;
            statsDirectionLabel.Text = "大单方向：【多空平衡 ─】";
            statsDirectionLabel.Click += statsDirectionLabel_Click;
            // 
            // abnormalGrid
            // 
            abnormalGrid.AllowUserToAddRows = false;
            abnormalGrid.AllowUserToDeleteRows = false;
            abnormalGrid.Anchor = AnchorStyles.Top | AnchorStyles.Bottom | AnchorStyles.Left;
            abnormalGrid.ColumnHeadersHeightSizeMode = DataGridViewColumnHeadersHeightSizeMode.AutoSize;
            abnormalGrid.Font = new Font("Microsoft YaHei UI", 9F);
            abnormalGrid.Location = new Point(6, 125);
            abnormalGrid.Name = "abnormalGrid";
            abnormalGrid.ReadOnly = true;
            abnormalGrid.RowHeadersWidth = 62;
            abnormalGrid.RowTemplate.Height = 28;
            abnormalGrid.Size = new Size(724, 380);
            abnormalGrid.TabIndex = 9;
            // 
            // consecutiveGroupBox
            // 
            consecutiveGroupBox.Anchor = AnchorStyles.Bottom | AnchorStyles.Left;
            consecutiveGroupBox.Controls.Add(enableConsecutiveCheckBox);
            consecutiveGroupBox.Controls.Add(consecutiveWindowLabel);
            consecutiveGroupBox.Controls.Add(consecutiveWindowComboBox);
            consecutiveGroupBox.Controls.Add(consecutiveCountLabel);
            consecutiveGroupBox.Controls.Add(consecutiveCountNumeric);
            consecutiveGroupBox.Controls.Add(consecutiveThresholdLabel);
            consecutiveGroupBox.Controls.Add(consecutiveThresholdNumeric);
            consecutiveGroupBox.Controls.Add(consecutiveSameDirectionCheckBox);
            consecutiveGroupBox.Controls.Add(consecutiveStatsPanel);
            consecutiveGroupBox.Controls.Add(consecutiveHistoryGrid);
            consecutiveGroupBox.Font = new Font("Microsoft YaHei UI", 9F, FontStyle.Bold);
            consecutiveGroupBox.ForeColor = Color.DarkOrange;
            consecutiveGroupBox.Location = new Point(12, 850);
            consecutiveGroupBox.Name = "consecutiveGroupBox";
            consecutiveGroupBox.Size = new Size(740, 234);
            consecutiveGroupBox.TabIndex = 13;
            consecutiveGroupBox.TabStop = false;
            consecutiveGroupBox.Text = "【连续大单】";
            // 
            // enableConsecutiveCheckBox
            // 
            enableConsecutiveCheckBox.Checked = true;
            enableConsecutiveCheckBox.CheckState = CheckState.Checked;
            enableConsecutiveCheckBox.Font = new Font("Microsoft YaHei UI", 9F, FontStyle.Bold);
            enableConsecutiveCheckBox.Location = new Point(10, 25);
            enableConsecutiveCheckBox.Name = "enableConsecutiveCheckBox";
            enableConsecutiveCheckBox.Size = new Size(150, 24);
            enableConsecutiveCheckBox.TabIndex = 0;
            enableConsecutiveCheckBox.Text = "启用连续检测";
            // 
            // consecutiveWindowLabel
            // 
            consecutiveWindowLabel.Font = new Font("Microsoft YaHei UI", 9F);
            consecutiveWindowLabel.Location = new Point(10, 55);
            consecutiveWindowLabel.Name = "consecutiveWindowLabel";
            consecutiveWindowLabel.Size = new Size(90, 23);
            consecutiveWindowLabel.TabIndex = 1;
            consecutiveWindowLabel.Text = "检测窗口：";
            // 
            // consecutiveWindowComboBox
            // 
            consecutiveWindowComboBox.DropDownStyle = ComboBoxStyle.DropDownList;
            consecutiveWindowComboBox.Font = new Font("Microsoft YaHei UI", 9F);
            consecutiveWindowComboBox.FormattingEnabled = true;
            consecutiveWindowComboBox.Items.AddRange(new object[] { "30秒", "60秒", "90秒", "120秒", "180秒" });
            consecutiveWindowComboBox.Location = new Point(100, 52);
            consecutiveWindowComboBox.Name = "consecutiveWindowComboBox";
            consecutiveWindowComboBox.Size = new Size(80, 25);
            consecutiveWindowComboBox.TabIndex = 2;
            // 
            // consecutiveCountLabel
            // 
            consecutiveCountLabel.Font = new Font("Microsoft YaHei UI", 9F);
            consecutiveCountLabel.Location = new Point(190, 55);
            consecutiveCountLabel.Name = "consecutiveCountLabel";
            consecutiveCountLabel.Size = new Size(90, 23);
            consecutiveCountLabel.TabIndex = 3;
            consecutiveCountLabel.Text = "最小笔数：";
            // 
            // consecutiveCountNumeric
            // 
            consecutiveCountNumeric.Font = new Font("Microsoft YaHei UI", 9F);
            consecutiveCountNumeric.Location = new Point(280, 52);
            consecutiveCountNumeric.Maximum = new decimal(new int[] { 20, 0, 0, 0 });
            consecutiveCountNumeric.Minimum = new decimal(new int[] { 2, 0, 0, 0 });
            consecutiveCountNumeric.Name = "consecutiveCountNumeric";
            consecutiveCountNumeric.Size = new Size(70, 23);
            consecutiveCountNumeric.TabIndex = 4;
            consecutiveCountNumeric.Value = new decimal(new int[] { 3, 0, 0, 0 });
            // 
            // consecutiveThresholdLabel
            // 
            consecutiveThresholdLabel.AutoSize = true;
            consecutiveThresholdLabel.BackColor = SystemColors.ButtonHighlight;
            consecutiveThresholdLabel.Font = new Font("Microsoft YaHei UI", 9F);
            consecutiveThresholdLabel.ForeColor = Color.Tomato;
            consecutiveThresholdLabel.Location = new Point(360, 55);
            consecutiveThresholdLabel.Name = "consecutiveThresholdLabel";
            consecutiveThresholdLabel.Size = new Size(56, 17);
            consecutiveThresholdLabel.TabIndex = 5;
            consecutiveThresholdLabel.Text = "最小量：";
            consecutiveThresholdLabel.Click += consecutiveThresholdLabel_Click;
            // 
            // consecutiveThresholdNumeric
            // 
            consecutiveThresholdNumeric.DecimalPlaces = 2;
            consecutiveThresholdNumeric.Font = new Font("Microsoft YaHei UI", 9F);
            consecutiveThresholdNumeric.Increment = new decimal(new int[] { 5, 0, 0, 131072 });
            consecutiveThresholdNumeric.Location = new Point(448, 52);
            consecutiveThresholdNumeric.Maximum = new decimal(new int[] { 1000, 0, 0, 0 });
            consecutiveThresholdNumeric.Minimum = new decimal(new int[] { 1, 0, 0, 131072 });
            consecutiveThresholdNumeric.Name = "consecutiveThresholdNumeric";
            consecutiveThresholdNumeric.Size = new Size(90, 23);
            consecutiveThresholdNumeric.TabIndex = 6;
            consecutiveThresholdNumeric.Value = new decimal(new int[] { 5, 0, 0, 131072 });
            // 
            // consecutiveSameDirectionCheckBox
            // 
            consecutiveSameDirectionCheckBox.Checked = true;
            consecutiveSameDirectionCheckBox.CheckState = CheckState.Checked;
            consecutiveSameDirectionCheckBox.Font = new Font("Microsoft YaHei UI", 9F);
            consecutiveSameDirectionCheckBox.Location = new Point(570, 56);
            consecutiveSameDirectionCheckBox.Name = "consecutiveSameDirectionCheckBox";
            consecutiveSameDirectionCheckBox.Size = new Size(160, 24);
            consecutiveSameDirectionCheckBox.TabIndex = 5;
            consecutiveSameDirectionCheckBox.Text = "只统计同方向";
            // 
            // consecutiveStatsPanel
            // 
            consecutiveStatsPanel.BackColor = Color.FromArgb(255, 250, 240);
            consecutiveStatsPanel.BorderStyle = BorderStyle.FixedSingle;
            consecutiveStatsPanel.Controls.Add(consecutiveBuyCountLabel);
            consecutiveStatsPanel.Controls.Add(consecutiveBuyVolumeLabel);
            consecutiveStatsPanel.Controls.Add(consecutiveBuyStatusLabel);
            consecutiveStatsPanel.Controls.Add(consecutiveSellCountLabel);
            consecutiveStatsPanel.Controls.Add(consecutiveSellVolumeLabel);
            consecutiveStatsPanel.Controls.Add(consecutiveSellStatusLabel);
            consecutiveStatsPanel.Location = new Point(10, 85);
            consecutiveStatsPanel.Name = "consecutiveStatsPanel";
            consecutiveStatsPanel.Size = new Size(720, 55);
            consecutiveStatsPanel.TabIndex = 6;
            // 
            // consecutiveBuyCountLabel
            // 
            consecutiveBuyCountLabel.Font = new Font("Microsoft YaHei UI", 9F);
            consecutiveBuyCountLabel.ForeColor = Color.DarkGreen;
            consecutiveBuyCountLabel.Location = new Point(10, 5);
            consecutiveBuyCountLabel.Name = "consecutiveBuyCountLabel";
            consecutiveBuyCountLabel.Size = new Size(200, 23);
            consecutiveBuyCountLabel.TabIndex = 0;
            consecutiveBuyCountLabel.Text = "买入: 0/3笔";
            // 
            // consecutiveBuyVolumeLabel
            // 
            consecutiveBuyVolumeLabel.Font = new Font("Microsoft YaHei UI", 9F);
            consecutiveBuyVolumeLabel.ForeColor = Color.DarkGreen;
            consecutiveBuyVolumeLabel.Location = new Point(220, 5);
            consecutiveBuyVolumeLabel.Name = "consecutiveBuyVolumeLabel";
            consecutiveBuyVolumeLabel.Size = new Size(200, 23);
            consecutiveBuyVolumeLabel.TabIndex = 1;
            consecutiveBuyVolumeLabel.Text = "总量: 0.00 BTC";
            // 
            // consecutiveBuyStatusLabel
            // 
            consecutiveBuyStatusLabel.Font = new Font("Microsoft YaHei UI", 9F, FontStyle.Bold);
            consecutiveBuyStatusLabel.ForeColor = Color.Gray;
            consecutiveBuyStatusLabel.Location = new Point(426, 5);
            consecutiveBuyStatusLabel.Name = "consecutiveBuyStatusLabel";
            consecutiveBuyStatusLabel.Size = new Size(139, 23);
            consecutiveBuyStatusLabel.TabIndex = 2;
            consecutiveBuyStatusLabel.Text = "[✗未触发] 还需3笔";
            // 
            // consecutiveSellCountLabel
            // 
            consecutiveSellCountLabel.Font = new Font("Microsoft YaHei UI", 9F);
            consecutiveSellCountLabel.ForeColor = Color.DarkRed;
            consecutiveSellCountLabel.Location = new Point(9, 28);
            consecutiveSellCountLabel.Name = "consecutiveSellCountLabel";
            consecutiveSellCountLabel.Size = new Size(200, 23);
            consecutiveSellCountLabel.TabIndex = 3;
            consecutiveSellCountLabel.Text = "卖出: 0/3笔";
            // 
            // consecutiveSellVolumeLabel
            // 
            consecutiveSellVolumeLabel.Font = new Font("Microsoft YaHei UI", 9F);
            consecutiveSellVolumeLabel.ForeColor = Color.DarkRed;
            consecutiveSellVolumeLabel.Location = new Point(220, 28);
            consecutiveSellVolumeLabel.Name = "consecutiveSellVolumeLabel";
            consecutiveSellVolumeLabel.Size = new Size(200, 23);
            consecutiveSellVolumeLabel.TabIndex = 4;
            consecutiveSellVolumeLabel.Text = "总量: 0.00 BTC";
            // 
            // consecutiveSellStatusLabel
            // 
            consecutiveSellStatusLabel.Font = new Font("Microsoft YaHei UI", 9F, FontStyle.Bold);
            consecutiveSellStatusLabel.ForeColor = Color.Gray;
            consecutiveSellStatusLabel.Location = new Point(426, 28);
            consecutiveSellStatusLabel.Name = "consecutiveSellStatusLabel";
            consecutiveSellStatusLabel.Size = new Size(270, 23);
            consecutiveSellStatusLabel.TabIndex = 5;
            consecutiveSellStatusLabel.Text = "[✗未触发] 还需3笔";
            // 
            // consecutiveHistoryGrid
            // 
            consecutiveHistoryGrid.AllowUserToAddRows = false;
            consecutiveHistoryGrid.AllowUserToDeleteRows = false;
            consecutiveHistoryGrid.Anchor = AnchorStyles.Top | AnchorStyles.Bottom | AnchorStyles.Left;
            consecutiveHistoryGrid.ColumnHeadersHeightSizeMode = DataGridViewColumnHeadersHeightSizeMode.AutoSize;
            consecutiveHistoryGrid.Font = new Font("Microsoft YaHei UI", 9F);
            consecutiveHistoryGrid.Location = new Point(10, 146);
            consecutiveHistoryGrid.Name = "consecutiveHistoryGrid";
            consecutiveHistoryGrid.ReadOnly = true;
            consecutiveHistoryGrid.RowHeadersWidth = 62;
            consecutiveHistoryGrid.RowTemplate.Height = 28;
            consecutiveHistoryGrid.Size = new Size(724, 79);
            consecutiveHistoryGrid.TabIndex = 7;
            // 
            // connectionStatusLabel
            // 
            connectionStatusLabel.AutoSize = true;
            connectionStatusLabel.Font = new Font("Microsoft YaHei UI", 9F, FontStyle.Bold);
            connectionStatusLabel.ForeColor = Color.DarkGreen;
            connectionStatusLabel.Location = new Point(642, 20);
            connectionStatusLabel.Name = "connectionStatusLabel";
            connectionStatusLabel.Size = new Size(104, 17);
            connectionStatusLabel.TabIndex = 100;
            connectionStatusLabel.Text = "连接状态：未连接";
            // 
            // viewStatisticsButton
            // 
            viewStatisticsButton.Font = new Font("Microsoft YaHei UI", 9F);
            viewStatisticsButton.Location = new Point(942, 12);
            viewStatisticsButton.Name = "viewStatisticsButton";
            viewStatisticsButton.Size = new Size(143, 30);
            viewStatisticsButton.TabIndex = 102;
            viewStatisticsButton.Text = "查看市价比统计";
            viewStatisticsButton.UseVisualStyleBackColor = true;
            viewStatisticsButton.Click += ViewStatisticsButton_Click;
            // 
            // viewLargeOrderStatisticsButton
            // 
            viewLargeOrderStatisticsButton.Font = new Font("Microsoft YaHei UI", 9F);
            viewLargeOrderStatisticsButton.Location = new Point(1091, 12);
            viewLargeOrderStatisticsButton.Name = "viewLargeOrderStatisticsButton";
            viewLargeOrderStatisticsButton.Size = new Size(143, 30);
            viewLargeOrderStatisticsButton.TabIndex = 103;
            viewLargeOrderStatisticsButton.Text = "查看大单统计";
            viewLargeOrderStatisticsButton.UseVisualStyleBackColor = true;
            viewLargeOrderStatisticsButton.Click += ViewLargeOrderStatisticsButton_Click;
            // 
            // viewAbnormalDetailButton
            // 
            viewAbnormalDetailButton.Font = new Font("Microsoft YaHei UI", 9F);
            viewAbnormalDetailButton.Location = new Point(942, 51);
            viewAbnormalDetailButton.Name = "viewAbnormalDetailButton";
            viewAbnormalDetailButton.Size = new Size(143, 30);
            viewAbnormalDetailButton.TabIndex = 106;
            viewAbnormalDetailButton.Text = "异常大单监控明细";
            viewAbnormalDetailButton.UseVisualStyleBackColor = true;
            viewAbnormalDetailButton.Click += ViewAbnormalDetailButton_Click;
            // 
            // priceTickComboBox
            // 
            priceTickComboBox.DropDownStyle = ComboBoxStyle.DropDownList;
            priceTickComboBox.Font = new Font("Microsoft YaHei UI", 9F);
            priceTickComboBox.FormattingEnabled = true;
            priceTickComboBox.Items.AddRange(new object[] { "0.01 - 精确到分", "0.1 - 精确到角", "1 - 精确到元", "5 - 5元档位", "10 - 10元档位", "50 - 50元档位", "100 - 100元档位" });
            priceTickComboBox.Location = new Point(582, 112);
            priceTickComboBox.Name = "priceTickComboBox";
            priceTickComboBox.Size = new Size(137, 25);
            priceTickComboBox.TabIndex = 105;
            priceTickComboBox.SelectedIndexChanged += PriceTickComboBox_SelectedIndexChanged;
            // 
            // MainForm
            // 
            ClientSize = new Size(1287, 1061);
            Controls.Add(label1);
            Controls.Add(symbolBox);
            Controls.Add(connectButton);
            Controls.Add(useProxyCheckBox);
            Controls.Add(proxyTextBox);
            Controls.Add(connectionStatusLabel);
            Controls.Add(viewStatisticsButton);
            Controls.Add(viewLargeOrderStatisticsButton);
            Controls.Add(viewAbnormalDetailButton);
            Controls.Add(priceTickComboBox);
            Controls.Add(consecutiveGroupBox);
            Controls.Add(tradeTitleLabel);
            Controls.Add(tradeGrid);
            Controls.Add(orderTitleLabel);
            Controls.Add(sellTitleLabel);
            Controls.Add(sellGrid);
            Controls.Add(buyTitleLabel);
            Controls.Add(buyGrid);
            Controls.Add(abnormalGroupBox);
            Name = "MainForm";
            Text = "【合约监控】市价比 & 大单 & 爆单";
            Load += MainForm_Load;
            ((System.ComponentModel.ISupportInitialize)tradeGrid).EndInit();
            ((System.ComponentModel.ISupportInitialize)buyGrid).EndInit();
            ((System.ComponentModel.ISupportInitialize)sellGrid).EndInit();
            abnormalGroupBox.ResumeLayout(false);
            ((System.ComponentModel.ISupportInitialize)multipleNumeric).EndInit();
            ((System.ComponentModel.ISupportInitialize)thresholdNumeric).EndInit();
            statsPanel.ResumeLayout(false);
            ((System.ComponentModel.ISupportInitialize)abnormalGrid).EndInit();
            consecutiveGroupBox.ResumeLayout(false);
            consecutiveGroupBox.PerformLayout();
            ((System.ComponentModel.ISupportInitialize)consecutiveCountNumeric).EndInit();
            ((System.ComponentModel.ISupportInitialize)consecutiveThresholdNumeric).EndInit();
            consecutiveStatsPanel.ResumeLayout(false);
            ((System.ComponentModel.ISupportInitialize)consecutiveHistoryGrid).EndInit();
            ResumeLayout(false);
            PerformLayout();
        }
    }
}
